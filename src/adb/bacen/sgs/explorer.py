"""
Explorer SGS - Interface pythonica para query de series temporais BCB.

Uso:
    from adb.core.data import sgs

    df = sgs.read('selic')
    df = sgs.read('selic', start='2020', end='2023')
    df = sgs.read('selic', 'cdi', 'dolar_ptax')
    print(sgs.available())
"""

from adb.core.data.explorers import BaseExplorer
from .indicators import SGS_CONFIG


class SGSExplorer(BaseExplorer):
    """
    Explorer para dados SGS.

    Fornece interface pythonica para leitura de series temporais
    do Sistema Gerenciador de Series Temporais do BCB.
    """

    _CONFIG = SGS_CONFIG
    _SUBDIR = "bacen/sgs/daily"

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna a classe do coletor associado."""
        from adb.bacen.sgs.collector import SGSCollector
        return SGSCollector

    # =========================================================================
    # Metodos auxiliares
    # =========================================================================

    def _get_subdir(self, indicator: str) -> str:
        """SGS tem subdir dinamico baseado em frequency."""
        return f"bacen/sgs/{self._CONFIG[indicator]['frequency']}"
