import pandas as pd
from ..styling.theme import theme

def plot_bar(ax, x, y_data, y_origin: str = 'zero', **kwargs):
    if 'color' not in kwargs:
        kwargs['color'] = theme.colors.primary

    # Largura da barra inteligente baseada na frequencia dos dados
    width = 0.8
    if pd.api.types.is_datetime64_any_dtype(x):
        if len(x) > 1:
            avg_diff = (x.max() - x.min()) / (len(x) - 1)
            if avg_diff.days > 25:
                width = 20  # Mensal
            elif avg_diff.days > 300:
                width = 300  # Anual

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
