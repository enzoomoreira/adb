"""
Módulo utilitário para execução paralela de tarefas.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, TypeVar, Any

T = TypeVar("T")  # Tipo do item de entrada
R = TypeVar("R")  # Tipo do resultado


class ParallelFetcher:
    """
    Executor paralelo genérico para tarefas de I/O bound (como downloads).

    Exemplo de uso:
        fetcher = ParallelFetcher(max_workers=4)
        results = fetcher.fetch_all(urls, download_func)
    """

    def __init__(
        self, max_workers: int = 4, on_item_complete: Callable[[T, R], None] = None
    ):
        """
        Inicializa o executor.

        Args:
            max_workers: Número máximo de threads em paralelo.
            on_item_complete: Callback opcional executado após cada tarefa.
                            Assinatura: (item, resultado) -> None
        """
        self.max_workers = max_workers
        self.on_item_complete = on_item_complete

    def fetch_all(self, items: Iterable[T], fetch_fn: Callable[[T], R]) -> dict[T, R]:
        """
        Executa fetch_fn para cada item em paralelo.

        Args:
            items: Lista de itens para processar (ex: datas, ids, urls).
            fetch_fn: Função que processa um item e retorna um resultado.

        Returns:
            Dicionário {item: resultado}
        """
        results = {}

        # Se max_workers for 1 ou menos, executa sequencialmente (debug/fallback)
        if self.max_workers <= 1:
            for item in items:
                try:
                    result = fetch_fn(item)
                    results[item] = result
                    if self.on_item_complete:
                        self.on_item_complete(item, result)
                except Exception as e:
                    print(f"Erro ao processar {item}: {e}")
                    results[item] = None  # ou raise, dependendo da estratégia
            return results

        # Execução paralela
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Mapeia futures de volta para os itens originais
            future_to_item = {executor.submit(fetch_fn, item): item for item in items}

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results[item] = result

                    if self.on_item_complete:
                        self.on_item_complete(item, result)

                except Exception as e:
                    print(f"Erro na thread para {item}: {e}")
                    results[item] = None

        return results
