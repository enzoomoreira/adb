import numpy as np
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

    annot = ax.annotate(label_text,
               xy=(last_date, last_val),
               xytext=(5, 0),
               textcoords='offset points',
               color=color,
               fontproperties=theme.font,
               fontweight='bold',
               va='center')

    # Registra annotation para deteccao de colisao
    if not hasattr(ax, '_agora_annotations'):
        ax._agora_annotations = []
    ax._agora_annotations.append(annot)


def highlight_last_bar(ax, x, series: pd.Series, color: str = None, **kwargs):
    """
    Destaca o valor da ultima barra com um label no topo.

    Ignora silenciosamente se a serie estiver vazia ou o ultimo valor for NaN/Inf.

    Args:
        ax: Matplotlib Axes
        x: Dados do eixo X (posicoes das barras)
        series: Series com os valores das barras
        color: Cor do texto (default: cor primaria do tema)
    """
    if series.empty:
        return

    # Encontra o ultimo valor valido (nao-NaN)
    valid_series = series.dropna()
    if valid_series.empty:
        return

    last_idx = valid_series.index[-1]
    last_val = valid_series.iloc[-1]

    # Verifica se o valor e finito (nao Inf)
    if not np.isfinite(last_val):
        return

    if color is None:
        color = theme.colors.primary

    # Encontra a posicao X correspondente ao ultimo indice
    # Se x for DatetimeIndex, procura pelo indice; senao usa posicao
    if hasattr(x, 'get_loc'):
        try:
            x_pos = x.get_loc(last_idx)
            x_val = x[x_pos]
        except KeyError:
            x_val = last_idx
    else:
        x_val = last_idx

    # Formata valor usando o formatter do eixo Y
    y_fmt = ax.yaxis.get_major_formatter()
    label_text = y_fmt(last_val, None)

    if not label_text:
        label_text = f"{last_val:.2f}"

    # Offset vertical: acima da barra se positivo, abaixo se negativo
    offset_y = 8 if last_val >= 0 else -8
    va = 'bottom' if last_val >= 0 else 'top'

    annot = ax.annotate(label_text,
               xy=(x_val, last_val),
               xytext=(0, offset_y),
               textcoords='offset points',
               color=color,
               fontproperties=theme.font,
               fontweight='bold',
               ha='center',
               va=va)

    # Registra annotation para deteccao de colisao
    if not hasattr(ax, '_agora_annotations'):
        ax._agora_annotations = []
    ax._agora_annotations.append(annot)
