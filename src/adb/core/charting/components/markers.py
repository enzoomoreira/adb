import pandas as pd
from ..styling.theme import theme

def highlight_last_point(ax, series: pd.Series, color: str = None, **kwargs):
    """
    Destaca o ultimo ponto da serie com um scatter e label.

    Ignora silenciosamente se a serie estiver vazia ou o ultimo valor for NaN/Inf.
    """
    if series.empty:
        return

    # Encontra o ultimo valor valido (nao-NaN)
    valid_series = series.dropna()
    if valid_series.empty:
        return

    last_date = valid_series.index[-1]
    last_val = valid_series.iloc[-1]

    # Verifica se o valor e finito (nao Inf)
    if not pd.isna(last_val) and pd.api.types.is_number(last_val):
        import numpy as np
        if not np.isfinite(last_val):
            return

    if color is None:
        color = theme.colors.primary

    # Scatter (bolinha)
    ax.scatter([last_date], [last_val], color=color, s=30, zorder=5)
    
    # Texto
    # Formata valor (tenta usar o formatter do eixo Y se disponivel, senao default)
    y_fmt = ax.yaxis.get_major_formatter()
    label_text = y_fmt(last_val, None) 
    
    # Se o formatter for ScalarFormatter padrao do mpl, ele pode retornar string vazia ou cientifica feia
    # Entao fallback simples se parecer ruim
    if not label_text: 
        label_text = f"{last_val:.2f}"

    ax.annotate(label_text, 
               xy=(last_date, last_val),
               xytext=(5, 0), 
               textcoords='offset points',
               color=color,
               fontproperties=theme.font,
               fontweight='bold',
               va='center')
