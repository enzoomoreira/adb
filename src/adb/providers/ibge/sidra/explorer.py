"""Explorer Sidra - Interface para series IBGE."""

from adb.explorer import BaseExplorer
from .indicators import SIDRA_CONFIG


class SidraExplorer(BaseExplorer):
    """Explorer para dados do Sistema IBGE de Recuperacao Automatica."""

    _CONFIG = SIDRA_CONFIG
    _SUBDIR_TEMPLATE = "ibge/sidra/{frequency}"
    _TITLE = "IBGE - Sistema SIDRA"

    @property
    def _CLIENT_CLASS(self):
        from adb.providers.ibge.sidra.client import SidraClient

        return SidraClient
