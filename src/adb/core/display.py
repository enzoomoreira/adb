"""
Sistema de display para output visual ao usuario.

Separa feedback visual (console) de logging tecnico (arquivo).
Para logging tecnico, use get_logger() de core.log.
"""

import sys
import threading
from typing import TextIO, Iterator, Iterable, TypeVar

from tqdm.auto import tqdm

T = TypeVar('T')


# =============================================================================
# Cores ANSI
# =============================================================================

class _Colors:
    """
    Codigos ANSI para cores no terminal.

    Suporta deteccao automatica de TTY e habilita VIRTUAL_TERMINAL_PROCESSING
    no Windows para compatibilidade com cores ANSI.
    """

    # Codigos de cores
    RESET = '\033[0m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'

    # Cache do resultado de enabled() - avaliado uma vez
    _enabled: bool | None = None

    @classmethod
    def enabled(cls) -> bool:
        """
        Verifica se cores ANSI sao suportadas no terminal atual.

        Resultado e cacheado apos primeira chamada, pois suporte a cores
        nao muda durante execucao.

        Returns:
            True se cores sao suportadas, False caso contrario.
        """
        if cls._enabled is not None:
            return cls._enabled

        # Verifica se stdout e um TTY (nao redirecionado para arquivo)
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            cls._enabled = False
            return cls._enabled

        # No Windows, precisamos habilitar VIRTUAL_TERMINAL_PROCESSING
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # STD_OUTPUT_HANDLE = -11
                handle = kernel32.GetStdHandle(-11)
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(handle, ctypes.byref(mode))
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
                cls._enabled = True
            except Exception:
                # Fallback se falhar (terminal antigo ou sem suporte)
                cls._enabled = False
        else:
            # Em sistemas Unix-like, TTY geralmente suporta cores
            cls._enabled = True

        return cls._enabled


# =============================================================================
# Progress Bar Wrapper
# =============================================================================

class _ProgressBar(Iterator[T]):
    """
    Wrapper em volta do tqdm que notifica o Display quando inicia/finaliza.

    Isso permite que Display._print() use tqdm.write() automaticamente
    quando ha barras de progresso ativas, evitando output corrompido.
    """

    def __init__(
        self,
        iterable: Iterable[T],
        display: 'Display',
        total: int = None,
        desc: str = None,
        unit: str = "it",
        leave: bool = False,
    ):
        self._display = display
        self._pbar = tqdm(
            iterable,
            total=total,
            desc=desc,
            unit=unit,
            leave=leave,
            disable=not display.verbose,
            file=display.stream,
        )
        # Obter iterador do tqdm (necessario para tqdm_asyncio)
        self._iter = iter(self._pbar)
        # Incrementa contador de barras ativas (thread-safe)
        with self._display._bars_lock:
            self._display._active_bars += 1

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        try:
            return next(self._iter)
        except StopIteration:
            self.close()
            raise

    def close(self):
        """Fecha a barra e decrementa contador."""
        if self._pbar is not None:
            self._pbar.close()
            # Decrementa contador de barras ativas (thread-safe)
            with self._display._bars_lock:
                self._display._active_bars = max(0, self._display._active_bars - 1)
            self._pbar = None

    def __enter__(self) -> '_ProgressBar[T]':
        return self

    def __exit__(self, *args):
        self.close()


class Display:
    """
    Gerencia output visual para o usuario.

    Responsabilidades:
    - Banners e separadores
    - Mensagens de progresso e status
    - Barras de progresso (via tqdm)
    - Formatacao consistente
    - Cores ANSI para destaque (warning/error/banners)

    Thread-safety:
    - Usa tqdm.write() quando ha barras ativas (evita output corrompido)
    - Contador de barras protegido por lock

    Para logging tecnico (arquivo), use get_logger() de core.log.

    Args:
        verbose: Se True, exibe mensagens. Se False, silencia tudo.
        stream: Stream de saida (default: sys.stdout).
        colors: Se True, usa cores ANSI quando suportado.

    Exemplo:
        display = Display(verbose=True)
        display.banner("BACEN - SGS", indicator_count=10, first_run=True)
        display.fetch_start("selic", "2024-01-01")
        display.fetch_result(275)
        display.end_banner(total=275)

        # Com barra de progresso
        for item in display.progress(items, total=100, desc="Processando"):
            process(item)
    """

    def __init__(
        self,
        verbose: bool = True,
        stream: TextIO = None,
        colors: bool = True,
    ):
        self.verbose = verbose
        self.stream = stream or sys.stdout
        self._use_colors = colors and _Colors.enabled()

        # Thread-safety para barras de progresso
        self._active_bars = 0
        self._bars_lock = threading.Lock()

    def set_verbose(self, verbose: bool):
        """
        Altera estado verbose em runtime.

        Args:
            verbose: Se True, exibe mensagens. Se False, silencia.
        """
        self.verbose = verbose

    def _colorize(self, text: str, color: str) -> str:
        """
        Aplica cor ANSI ao texto se cores estiverem habilitadas.

        Args:
            text: Texto a colorir.
            color: Codigo de cor ANSI (ex: _Colors.YELLOW).

        Returns:
            Texto com codigos de cor ou texto original se cores desabilitadas.
        """
        if self._use_colors:
            return f"{color}{text}{_Colors.RESET}"
        return text

    def _print(self, message: str = ""):
        """
        Print interno com controle de verbose e compatibilidade com tqdm.

        Quando ha barras de progresso ativas, usa tqdm.write() para evitar
        que o output quebre a renderizacao das barras.
        """
        if not self.verbose:
            return

        # Se ha barras ativas, usar tqdm.write para nao corromper output
        if self._active_bars > 0:
            tqdm.write(message, file=self.stream)
        else:
            print(message, file=self.stream)

    # =========================================================================
    # Progress Bar
    # =========================================================================

    def progress(
        self,
        iterable: Iterable[T],
        total: int = None,
        desc: str = None,
        unit: str = "it",
        leave: bool = False,
    ) -> _ProgressBar[T]:
        """
        Retorna iterador com barra de progresso.

        Quando ha barra ativa, todos os metodos de print do Display
        usam tqdm.write() automaticamente para evitar output corrompido.

        Args:
            iterable: Iteravel a percorrer
            total: Numero total de itens (obrigatorio se iterable nao tem __len__)
            desc: Descricao exibida a esquerda da barra
            unit: Unidade dos itens (ex: "arquivo", "registro")
            leave: Se True, mantem barra apos conclusao

        Returns:
            Iterador que exibe progresso e pode ser usado em for-loops.

        Exemplo:
            for item in display.progress(items, total=100, desc="Baixando"):
                download(item)

            # Ou com context manager para garantir close():
            with display.progress(futures, total=10) as pbar:
                for future in pbar:
                    result = future.result()
        """
        return _ProgressBar(
            iterable=iterable,
            display=self,
            total=total,
            desc=desc,
            unit=unit,
            leave=leave,
        )

    # =========================================================================
    # Banners
    # =========================================================================

    def banner(
        self,
        title: str,
        subtitle: str = None,
        first_run: bool = None,
        indicator_count: int = None,
    ):
        """
        Exibe banner de inicio de coleta.

        Args:
            title: Titulo principal (ex: "BACEN - Sistema Gerenciador de Series")
            subtitle: Subtitulo opcional
            first_run: Se True, mostra "PRIMEIRA EXECUCAO". Se False, "ATUALIZACAO".
                       Se None, nao mostra status de execucao.
            indicator_count: Numero de indicadores a coletar
        """
        separator = self._colorize("=" * 70, _Colors.GREEN)
        self._print(separator)

        if first_run is not None:
            if first_run:
                self._print("PRIMEIRA EXECUCAO - Download de Historico Completo")
            else:
                self._print("ATUALIZACAO INCREMENTAL")
            self._print(separator)

        self._print(title)

        if subtitle:
            self._print(subtitle)

        self._print(separator)

        if indicator_count is not None:
            self._print(f"Indicadores a coletar: {indicator_count}")

        self._print()

    def end_banner(self, total: int = None):
        """
        Exibe banner de conclusao.

        Args:
            total: Total de registros coletados (opcional)
        """
        separator = self._colorize("=" * 70, _Colors.GREEN)
        self._print(separator)

        if total is not None:
            self._print(f"Coleta concluida! Total: {total:,} registros")
        else:
            self._print("Coleta concluida!")

        self._print(separator)

    def separator(self):
        """Exibe linha separadora."""
        self._print("-" * 70)

    # =========================================================================
    # Status de Fetch
    # =========================================================================

    def fetch_start(self, name: str, since: str = None):
        """
        Exibe inicio de fetch de indicador.

        Args:
            name: Nome do indicador
            since: Data de inicio (se incremental)
        """
        if since:
            self._print(f"  Buscando {name} desde {since}...")
        else:
            self._print(f"  Buscando {name} (historico completo)...")

    def fetch_result(self, count: int):
        """
        Exibe resultado de fetch.

        Args:
            count: Numero de registros obtidos
        """
        if count:
            self._print(f"  {count:,} registros")
        else:
            self._print(f"  Sem dados disponiveis")
        self._print()

    # =========================================================================
    # Arquivos
    # =========================================================================

    def saved(self, path: str):
        """
        Exibe arquivo salvo.

        Args:
            path: Caminho relativo do arquivo
        """
        self._print(f"Salvo: {path}")

    def appended(self, path: str):
        """
        Exibe arquivo atualizado (append).

        Args:
            path: Caminho relativo do arquivo
        """
        self._print(f"Append: {path}")

    # =========================================================================
    # Warnings e Errors
    # =========================================================================

    def warning(self, message: str):
        """
        Exibe warning para usuario (em amarelo se cores habilitadas).

        Args:
            message: Mensagem de aviso
        """
        colored_msg = self._colorize(f"  {message}", _Colors.YELLOW)
        self._print(colored_msg)

    def error(self, message: str):
        """
        Exibe erro para usuario (em vermelho se cores habilitadas).

        Args:
            message: Mensagem de erro
        """
        colored_msg = self._colorize(f"Erro: {message}", _Colors.RED)
        self._print(colored_msg)

    def info(self, message: str):
        """
        Exibe mensagem informativa.

        Args:
            message: Mensagem informativa
        """
        self._print(message)

    def __repr__(self) -> str:
        return f"Display(verbose={self.verbose}, colors={self._use_colors})"


# =============================================================================
# Singleton com Double-Checked Locking
# =============================================================================

_display_instance: Display | None = None
_display_lock = threading.Lock()


def get_display(verbose: bool = True) -> Display:
    """
    Retorna instancia unica de Display (Singleton thread-safe).

    Usa double-checked locking para performance:
    - Primeiro check sem lock (rapido, 99% dos casos)
    - Segundo check com lock (apenas na criacao)

    Args:
        verbose: Se True, exibe mensagens. Atualizado em cada chamada.

    Returns:
        Instancia singleton de Display.
    """
    global _display_instance

    # Primeiro check sem lock (fast path)
    if _display_instance is None:
        with _display_lock:
            # Segundo check com lock (evita race condition)
            if _display_instance is None:
                _display_instance = Display(verbose=verbose)

    # Atualiza verbose (operacao atomica em Python, safe sem lock)
    _display_instance.set_verbose(verbose)
    return _display_instance
