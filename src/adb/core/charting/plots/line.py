import pandas as pd
from ..styling.theme import theme
from ..components.markers import highlight_last_point

def plot_line(ax, x, y_data, highlight, **kwargs):
    # Se for Series, transforma em DF para unificar logica
    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    # Cores: usa paleta do tema
    colors = theme.colors.cycle()

    lines = []
    for i, col in enumerate(y_data.columns):
        # Define cor da linha atual
        if 'color' in kwargs:
            c = kwargs['color']
        else:
            c = colors[i % len(colors)]

        label = str(col)

        # Matplotlib 3.0+ aceita pandas diretamente
        line, = ax.plot(x, y_data[col], linewidth=2, color=c, label=label, **kwargs)
        lines.append(line)

        if highlight:
            highlight_last_point(ax, y_data[col], color=c)

    # Mostra legenda se houver mais de uma serie
    if y_data.shape[1] > 1:
        ax.legend(loc='best', frameon=True, framealpha=0.9)
