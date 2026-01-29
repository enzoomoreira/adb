"""
Linhas de referencia horizontais para graficos.

Inclui linhas ATH/ATL (All-Time High/Low) e linhas customizadas.
"""

import pandas as pd
from ..styling.theme import theme


def add_ath_line(
    ax,
    y_data: pd.Series | pd.DataFrame,
    color: str = None,
    linestyle: str = '--',
    label: str = 'ATH',
    linewidth: float = 1.5,
    series: str = None,
) -> None:
    """
    Adiciona linha horizontal no All-Time High (valor maximo).

    Args:
        ax: Matplotlib Axes
        y_data: Series ou DataFrame com os dados
        color: Cor da linha (default: theme.colors.positive)
        linestyle: Estilo da linha (default: '--')
        label: Rotulo da linha (default: 'ATH')
        linewidth: Espessura da linha (default: 1.5)
        series: Nome da coluna se y_data for DataFrame (default: primeira coluna)
    """
    # Resolve series se for DataFrame
    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        y_data = y_data[col]

    # Calcula ATH ignorando NaN
    ath_value = y_data.max()
    if pd.isna(ath_value):
        return  # Sem dados validos

    # Cor default: verde (positivo)
    line_color = color if color else theme.colors.positive

    ax.axhline(
        y=ath_value,
        color=line_color,
        linestyle=linestyle,
        linewidth=linewidth,
        label=label,
        zorder=1,  # Abaixo dos dados principais
    )


def add_atl_line(
    ax,
    y_data: pd.Series | pd.DataFrame,
    color: str = None,
    linestyle: str = '--',
    label: str = 'ATL',
    linewidth: float = 1.5,
    series: str = None,
) -> None:
    """
    Adiciona linha horizontal no All-Time Low (valor minimo).

    Args:
        ax: Matplotlib Axes
        y_data: Series ou DataFrame com os dados
        color: Cor da linha (default: theme.colors.negative)
        linestyle: Estilo da linha (default: '--')
        label: Rotulo da linha (default: 'ATL')
        linewidth: Espessura da linha (default: 1.5)
        series: Nome da coluna se y_data for DataFrame (default: primeira coluna)
    """
    # Resolve series se for DataFrame
    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        y_data = y_data[col]

    # Calcula ATL ignorando NaN
    atl_value = y_data.min()
    if pd.isna(atl_value):
        return  # Sem dados validos

    # Cor default: vermelho (negativo)
    line_color = color if color else theme.colors.negative

    ax.axhline(
        y=atl_value,
        color=line_color,
        linestyle=linestyle,
        linewidth=linewidth,
        label=label,
        zorder=1,
    )


def add_hline(
    ax,
    value: float,
    color: str = None,
    linestyle: str = '--',
    label: str = None,
    linewidth: float = 1.5,
) -> None:
    """
    Adiciona linha horizontal em valor arbitrario.

    Util para marcar metas, limites ou valores de referencia.

    Args:
        ax: Matplotlib Axes
        value: Valor Y onde a linha sera desenhada
        color: Cor da linha (default: theme.colors.grid)
        linestyle: Estilo da linha (default: '--')
        label: Rotulo da linha (opcional)
        linewidth: Espessura da linha (default: 1.5)

    Example:
        >>> add_hline(ax, 3.0, label='Meta de Inflacao', color='green')
    """
    # Cor default: cinza (grid)
    line_color = color if color else theme.colors.grid

    ax.axhline(
        y=value,
        color=line_color,
        linestyle=linestyle,
        linewidth=linewidth,
        label=label,
        zorder=1,
    )
