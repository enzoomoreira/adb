"""
Modulo de Charting do Agora-Database.

Fornece capacidades de plotagem padronizada via Pandas Accessor.

Uso:
    import adb.core.charting  # Registra o accessor 'agora'

    # Plotagem
    df.agora.plot()
    df.agora.plot(kind='bar', title='Titulo', units='%')

    # Transformacoes
    from adb.core.charting import yoy, mom, accum_12m
    df_yoy = yoy(df)
"""

from .accessor import AgoraAccessor
from .plotter import AgoraPlotter
from .theme import theme
from .transforms import yoy, mom, accum_12m, diff, normalize
from .config import CHARTS_PATH

__all__ = [
    'AgoraAccessor',
    'AgoraPlotter',
    'theme',
    'CHARTS_PATH',
    # Transforms
    'yoy',
    'mom',
    'accum_12m',
    'diff',
    'normalize',
]
