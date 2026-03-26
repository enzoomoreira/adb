"""Explorer IPEA - Interface para series IPEADATA."""

from adb.explorer import BaseExplorer
from .indicators import IPEA_CONFIG


class IPEAExplorer(BaseExplorer):
    """Explorer para series temporais agregadas do IPEADATA."""

    _CONFIG = IPEA_CONFIG
    _SUBDIR_TEMPLATE = "ipea/{frequency}"
    _TITLE = "IPEA - Instituto de Pesquisa Economica Aplicada"

    @property
    def _CLIENT_CLASS(self):
        from adb.providers.ipea.client import IPEAClient

        return IPEAClient
