import pandas as pd
from ..styling.theme import theme
from ..components.markers import highlight_last_bar

# Constantes para largura de barras baseada na frequencia dos dados
BAR_WIDTH_DEFAULT = 0.8
BAR_WIDTH_MONTHLY = 20
BAR_WIDTH_ANNUAL = 300
DAYS_THRESHOLD_ANNUAL = 300
DAYS_THRESHOLD_MONTHLY = 25


def plot_bar(ax, x, y_data, highlight: bool = False, y_origin: str = 'zero', **kwargs):
    """
    Plota grafico de barras com largura automatica baseada na frequencia.

    Args:
        ax: Matplotlib Axes
        x: Dados do eixo X (index ou coluna)
        y_data: Series ou DataFrame com dados do eixo Y
        highlight: Se True, destaca o ultimo valor com label
        y_origin: Origem do eixo Y ('zero' inclui zero, 'auto' foca nos dados)
        **kwargs: Argumentos extras para ax.bar()
    """
    if 'color' not in kwargs:
        kwargs['color'] = theme.colors.primary

    # Largura da barra inteligente baseada na frequencia dos dados
    width = BAR_WIDTH_DEFAULT
    if pd.api.types.is_datetime64_any_dtype(x):
        if len(x) > 1:
            avg_diff = (x.max() - x.min()) / (len(x) - 1)
            # Ordem importa: verificar anual primeiro (maior threshold)
            if avg_diff.days > DAYS_THRESHOLD_ANNUAL:
                width = BAR_WIDTH_ANNUAL
            elif avg_diff.days > DAYS_THRESHOLD_MONTHLY:
                width = BAR_WIDTH_MONTHLY

    if isinstance(y_data, pd.DataFrame):
        if y_data.shape[1] > 1:
            # Multiplas series: usa pandas plot
            y_data.plot(kind='bar', ax=ax, width=0.8, **kwargs)
            return
        else:
            vals = y_data.iloc[:, 0]
    else:
        vals = y_data

    ax.bar(x, vals, width=width, **kwargs)

    # Ajusta origem do eixo Y
    if y_origin == 'auto':
        # Ajusta eixo Y para focar nos dados com margem
        vals_clean = vals.dropna()
        if not vals_clean.empty:
            ymin, ymax = vals_clean.min(), vals_clean.max()
            margin = (ymax - ymin) * 0.1  # 10% de margem
            ax.set_ylim(ymin - margin, ymax + margin)
    else:
        # Default: inclui zero no eixo Y
        ymin, ymax = ax.get_ylim()
        if ymin > 0:
            ax.set_ylim(0, ymax)
        elif ymax < 0:
            ax.set_ylim(ymin, 0)

    # Destaca ultimo valor se solicitado
    if highlight:
        color = kwargs.get('color', theme.colors.primary)
        highlight_last_bar(ax, x, vals, color=color)
