import pandas as pd
import numpy as np
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

        # Converte para numpy para garantir compatibilidade com matplotlib
        x_np = x.to_numpy() if hasattr(x, 'to_numpy') else np.array(x)
        y_np = y_data[col].to_numpy() if hasattr(y_data[col], 'to_numpy') else np.array(y_data[col])

        line, = ax.plot(x_np, y_np, linewidth=2, color=c, label=label, **kwargs)
        lines.append(line)

        if highlight:
            highlight_last_point(ax, y_data[col], color=c)

    # Mostra legenda se houver mais de uma serie
    if y_data.shape[1] > 1:
        ax.legend(loc='best', frameon=True, framealpha=0.9)
