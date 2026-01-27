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
        """Retorna a classe do coletor associado."""
        from adb.bloomberg.collector import BloombergCollector
        return BloombergCollector
