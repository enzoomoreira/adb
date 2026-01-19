"""
Modulo de Charting do Agora-Database.

Fornece capacidades de plotagem padronizada via Pandas Accessor.

Uso:
    import core.charting # Registra o accessor 'agora'
    df.agora.plot()
"""

from .accessor import AgoraAccessor
from .plotter import AgoraPlotter
from .theme import apply_style

__all__ = ['AgoraAccessor', 'AgoraPlotter', 'apply_style']
