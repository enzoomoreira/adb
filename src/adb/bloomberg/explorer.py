"""
Explorer Bloomberg - Interface pythonica para query de dados de mercado.

Uso:
    from adb.core.data import bloomberg

    df = bloomberg.read('ibov_points')
    df = bloomberg.read('ibov_points', start='2020')
    print(bloomberg.available())

Nota: Requer Bloomberg Terminal para coleta, mas leitura funciona offline.
"""

from adb.core.data.explorers import BaseExplorer
from .indicators import BLOOMBERG_CONFIG


class BloombergExplorer(BaseExplorer):
    """
    Explorer para dados Bloomberg.

    Fornece interface pythonica para leitura de series temporais
    de mercado coletadas via Bloomberg Terminal.
    """

    _CONFIG = BLOOMBERG_CONFIG
    _SUBDIR = "bloomberg/daily"

    @property
    def _COLLECTOR_CLASS(self):
        from adb.bloomberg.collector import BloombergCollector
        return BloombergCollector

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        check_connection: bool = True,
        **kwargs,
    ) -> None:
        """
        Coleta dados de mercado via Bloomberg Terminal.

        Args:
            indicators: 'all', lista, ou string com indicador(es)
            save: Se True, salva em Parquet
            verbose: Se True, imprime progresso
            check_connection: Se True, valida conexao Bloomberg

        Raises:
            RuntimeError: Se Bloomberg nao disponivel e check_connection=True
        """
        collector = self._COLLECTOR_CLASS(check_connection=check_connection)
        collector.collect(indicators=indicators, save=save, verbose=verbose, **kwargs)

    def get_status(self):
        """Retorna status dos arquivos Bloomberg salvos."""
        collector = self._COLLECTOR_CLASS(check_connection=False)
        return collector.get_status()
