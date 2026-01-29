import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from .config import CHARTS_PATH
from .styling import theme, currency_formatter, percent_formatter, human_readable_formatter, points_formatter
from .components import add_footer, resolve_collisions
from .plots.line import plot_line
from .plots.bar import plot_bar
from .overlays import add_moving_average, add_ath_line, add_atl_line, add_hline, add_band

# Mapa de formatadores para eixo Y (Open/Closed: adicionar novos sem modificar _apply_y_formatter)
_FORMATTERS = {
    'BRL': lambda: currency_formatter('BRL'),
    'USD': lambda: currency_formatter('USD'),
    '%': percent_formatter,
    'human': human_readable_formatter,
    'points': points_formatter,
}


class AgoraPlotter:
    """
    Factory de visualizacao financeira padronizada.
    Orquestra temas, formatadores e componentes.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._fig = None
        self._ax = None
        
    # =========================================================================
    # API Publica
    # =========================================================================

    def plot(
        self,
        x: str = None,
        y: str | list[str] = None,
        kind: str = 'line',
        title: str = None,
        units: str = None,
        source: str = None,
        highlight_last: bool = False,
        y_origin: str = 'zero',
        save_path: str = None,
        moving_avg: int = None,
        show_ath: bool = False,
        show_atl: bool = False,
        overlays: dict = None,
        **kwargs
    ):
        """
        Gera um grafico padronizado.

        Args:
            x: Coluna para eixo X (default: index)
            y: Coluna(s) para eixo Y (default: todas numericas)
            kind: Tipo de grafico ('line' ou 'bar')
            title: Titulo do grafico
            units: Formatacao do eixo Y ('BRL', 'USD', '%', 'points', 'human')
            source: Fonte dos dados para rodape (ex: 'BCB', 'IBGE')
            highlight_last: Se True, destaca o ultimo valor da serie
            y_origin: Origem do eixo Y para barras ('zero', 'auto'). Default 'zero'.
            save_path: Caminho para salvar o grafico
            moving_avg: Janela da media movel (ex: 12 para MM12)
            show_ath: Se True, mostra linha no All-Time High
            show_atl: Se True, mostra linha no All-Time Low
            overlays: Dicionario com overlays customizados:
                - 'hlines': Lista de dicts com {value, label, color, linestyle}
                - 'band': Dict com {lower, upper, color, alpha, label}
            **kwargs: Argumentos extras para matplotlib

        Returns:
            matplotlib Axes
        """
        # 1. Setup inicial (Style)
        theme.apply()
        fig, ax = plt.subplots(figsize=(10, 6))
        self._fig = fig
        self._ax = ax
        
        # 2. Resolução de dados
        x_data = self.df.index if x is None else self.df[x]

        if y is None:
            y_data = self.df.select_dtypes(include=['number'])
        else:
            y_data = self.df[y]

        # 3. Aplica formatter ANTES da plotagem (para highlight_last usar o formatter correto)
        self._apply_y_formatter(ax, units)

        # 4. Plotagem Core
        if kind == 'line':
            plot_line(ax, x_data, y_data, highlight_last, **kwargs)
        elif kind == 'bar':
            plot_bar(ax, x_data, y_data, highlight=highlight_last, y_origin=y_origin, **kwargs)
        else:
            raise ValueError(f"Chart type '{kind}' not supported.")

        # 5. Aplicacao de Overlays
        self._apply_overlays(
            ax, x_data, y_data,
            moving_avg=moving_avg,
            show_ath=show_ath,
            show_atl=show_atl,
            overlays=overlays,
        )

        # 6. Resolver colisoes de labels
        resolve_collisions(ax)

        # 7. Aplicacao de Componentes e Decoracoes
        self._apply_title(ax, title)
        self._apply_decorations(fig, source)

        # 8. Output
        if save_path:
            self.save(save_path)
            
        return ax

    # =========================================================================
    # Helpers de Overlays
    # =========================================================================

    def _apply_overlays(
        self,
        ax,
        x_data,
        y_data,
        moving_avg: int = None,
        show_ath: bool = False,
        show_atl: bool = False,
        overlays: dict = None,
    ):
        """
        Aplica overlays sobre o grafico.

        Args:
            ax: Matplotlib Axes
            x_data: Dados do eixo X
            y_data: Dados do eixo Y (Series ou DataFrame)
            moving_avg: Janela da media movel
            show_ath: Mostrar linha ATH
            show_atl: Mostrar linha ATL
            overlays: Dicionario com overlays customizados
        """
        # Media movel
        if moving_avg:
            add_moving_average(ax, x_data, y_data, window=moving_avg)

        # All-Time High
        if show_ath:
            add_ath_line(ax, y_data)

        # All-Time Low
        if show_atl:
            add_atl_line(ax, y_data)

        # Overlays customizados via dicionario
        if overlays:
            # Linhas horizontais customizadas
            if 'hlines' in overlays:
                for hline_config in overlays['hlines']:
                    add_hline(
                        ax,
                        value=hline_config['value'],
                        label=hline_config.get('label'),
                        color=hline_config.get('color'),
                        linestyle=hline_config.get('linestyle', '--'),
                        linewidth=hline_config.get('linewidth', 1.5),
                    )

            # Banda sombreada
            if 'band' in overlays:
                band_config = overlays['band']
                add_band(
                    ax,
                    lower=band_config['lower'],
                    upper=band_config['upper'],
                    color=band_config.get('color'),
                    alpha=band_config.get('alpha', 0.15),
                    label=band_config.get('label'),
                )

    # =========================================================================
    # Helpers de Decoracao
    # =========================================================================

    def _apply_y_formatter(self, ax, units):
        """Aplica formatador no eixo Y baseado na unidade especificada."""
        if units and units in _FORMATTERS:
            ax.yaxis.set_major_formatter(_FORMATTERS[units]())

    def _apply_title(self, ax, title):
        """Aplica titulo centralizado."""
        if title:
            ax.set_title(title, loc='center', pad=20, fontproperties=theme.font, size=18, color=theme.colors.text, weight='bold')

    def _apply_decorations(self, fig, source):
        add_footer(fig, source)

    # =========================================================================
    # IO e Exportacao
    # =========================================================================

    def save(self, path: str, dpi: int = 300):
        """
        Salva o grafico atual em arquivo.

        Args:
            path: Caminho do arquivo (ex: 'grafico.png')
            dpi: Resolucao em DPI (default: 300)

        Raises:
            RuntimeError: Se nenhum grafico foi gerado ainda
        """
        if self._fig is None:
            raise RuntimeError("Nenhum grafico gerado. Chame plot() primeiro.")

        # Resolve path
        path_obj = Path(path)
        if not path_obj.is_absolute():
            CHARTS_PATH.mkdir(parents=True, exist_ok=True)
            path_obj = CHARTS_PATH / path_obj

        self._fig.savefig(path_obj, bbox_inches='tight', dpi=dpi)
