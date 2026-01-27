"""
Explorer SIDRA - Interface pythonica para query de series do IBGE.

Uso:
    from adb.core.data import sidra
    
    df = sidra.read('ipca')
    df = sidra.read('ipca', start='2020')
    print(sidra.available())
"""

from adb.core.data.explorers import BaseExplorer
from .indicators import SIDRA_CONFIG


class SidraExplorer(BaseExplorer):
    """
    Explorer para dados IBGE Sidra.
    
    Fornece interface pythonica para leitura de series temporais
    do Sistema IBGE de Recuperacao Automatica (SIDRA).
    """

    _CONFIG = SIDRA_CONFIG
    _SUBDIR = "ibge/sidra/monthly"

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna a classe do coletor associado."""
        from adb.ibge.sidra.collector import SidraCollector
        return SidraCollector

    # =========================================================================
    # Metodos auxiliares
    # =========================================================================

    def _subdir(self, indicator: str) -> str:
        """Sidra tem subdir dinamico baseado em frequency."""
        return f"ibge/sidra/{self._CONFIG[indicator].get('frequency', 'monthly')}"
