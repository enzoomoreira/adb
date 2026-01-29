"""
Modulo de Charting do Agora-Database.

Fornece capacidades de plotagem padronizada via Pandas Accessor.

Uso:
    import adb.core.charting  # Registra o accessor 'agora'

    # Plotagem
    df.agora.plot()
    df.agora.plot(kind='bar', title='Titulo', units='%')

    # Transformacoes
    from adb.core.charting import yoy, mom, accum_12m, annualize_daily
    df_yoy = yoy(df)
    cdi_anual = annualize_daily(cdi_diario)
"""

from .accessor import AgoraAccessor
from .engine import AgoraPlotter
from .styling.theme import theme
from .transforms import (
    yoy,
    mom,
    accum_12m,
    diff,
    normalize,
    annualize_daily,
    compound_rolling,
    real_rate,
    to_month_end,
)
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
    'annualize_daily',
    'compound_rolling',
    'real_rate',
    'to_month_end',
]
