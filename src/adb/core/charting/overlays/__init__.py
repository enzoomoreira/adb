"""
Overlays para graficos do Agora-Database.

Este modulo contem funcoes para adicionar elementos visuais secundarios
(overlays) sobre graficos, como medias moveis, linhas de referencia e bandas.
"""

from .moving_average import add_moving_average
from .reference_lines import add_ath_line, add_atl_line, add_hline
from .bands import add_band

__all__ = [
    'add_moving_average',
    'add_ath_line',
    'add_atl_line',
    'add_hline',
    'add_band',
]
