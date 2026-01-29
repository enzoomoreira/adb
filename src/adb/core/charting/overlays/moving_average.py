"""
Media movel para graficos.
"""

import pandas as pd


def add_moving_average(
    ax,
    x,
    y_data: pd.Series | pd.DataFrame,
    window: int,
    color: str = None,
    linestyle: str = '-',
    linewidth: float = 1.5,
    label: str = None,
    series: str = None,
) -> None:
    """
    Adiciona linha de media movel sobre os dados.

    Args:
        ax: Matplotlib Axes
        x: Dados do eixo X (index)
        y_data: Series ou DataFrame com os dados
        window: Janela da media movel (numero de periodos)
        color: Cor da linha (default: cinza)
        linestyle: Estilo da linha (default: '-')
        linewidth: Espessura da linha (default: 1.5)
        label: Rotulo para legenda (default: 'MM{window}')
        series: Nome da coluna se y_data for DataFrame (default: primeira coluna)

    Example:
        >>> add_moving_average(ax, df.index, df['valor'], window=12)
    """
    # Resolve series se for DataFrame
    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        y_data = y_data[col]

    # Calcula media movel
    ma = y_data.rolling(window=window, min_periods=1).mean()

    # Cor default: cinza para nao competir com dados principais
    line_color = color if color else '#888888'

    # Label default
    line_label = label if label else f'MM{window}'

    ax.plot(
        x,
        ma,
        color=line_color,
        linestyle=linestyle,
        linewidth=linewidth,
        label=line_label,
        zorder=2,  # Acima das linhas de referencia, abaixo dos dados principais
    )
