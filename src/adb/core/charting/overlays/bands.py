"""
Bandas sombreadas para graficos.
"""

from ..styling.theme import theme


def add_band(
    ax,
    lower: float,
    upper: float,
    color: str = None,
    alpha: float = 0.15,
    label: str = None,
) -> None:
    """
    Adiciona area sombreada entre dois valores horizontais.

    Util para representar bandas de tolerancia, intervalos de confianca,
    ou faixas de referencia.

    Args:
        ax: Matplotlib Axes
        lower: Limite inferior da banda
        upper: Limite superior da banda
        color: Cor da banda (default: theme.colors.grid)
        alpha: Transparencia da banda (default: 0.15)
        label: Rotulo para legenda (opcional)

    Example:
        >>> # Banda de meta de inflacao (1.5% a 4.5%)
        >>> add_band(ax, 1.5, 4.5, color='green', alpha=0.1, label='Meta')
    """
    # Cor default: cinza
    band_color = color if color else theme.colors.grid

    ax.axhspan(
        lower,
        upper,
        color=band_color,
        alpha=alpha,
        label=label,
        zorder=0,  # Abaixo de tudo
    )
