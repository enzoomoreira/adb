"""Explorer SGS - Interface para series temporais BCB."""

from adb.explorer import BaseExplorer
from .indicators import SGS_CONFIG


class SGSExplorer(BaseExplorer):
    """Explorer para dados SGS do Sistema Gerenciador de Series Temporais."""

    _CONFIG = SGS_CONFIG
    _SUBDIR_TEMPLATE = "bacen/sgs/{frequency}"
    _TITLE = "BACEN - Sistema Gerenciador de Series"

    @property
    def _CLIENT_CLASS(self):
        from adb.providers.bacen.sgs.client import SGSClient

        return SGSClient
