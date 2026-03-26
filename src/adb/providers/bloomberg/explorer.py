"""Explorer Bloomberg - Interface para dados de mercado."""

from adb.explorer import BaseExplorer
from .indicators import BLOOMBERG_CONFIG


class BloombergExplorer(BaseExplorer):
    """Explorer para dados Bloomberg. Requer Terminal para coleta, leitura funciona offline."""

    _CONFIG = BLOOMBERG_CONFIG
    _SUBDIR_TEMPLATE = "bloomberg/{frequency}"
    _TITLE = "BLOOMBERG - Market Data"

    @property
    def _CLIENT_CLASS(self):
        from adb.providers.bloomberg.client import BloombergClient

        return BloombergClient
