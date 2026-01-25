from ..styling.theme import theme

def add_footer(fig, source: str = None):
    """
    Adiciona rodape padrao ao grafico.

    Formato: "Fonte: {fonte}, Ágora Investimentos"
    Se fonte nao especificada: apenas "Ágora Investimentos"

    O footer e alinhado com a borda esquerda da area do grafico (axes).
    """
    if source:
        footer_text = f"Fonte: {source}, Ágora Investimentos"
    else:
        footer_text = "Ágora Investimentos"

    # Alinha com a borda esquerda do axes (area do grafico)
    x_pos = 0.01
    if fig.axes:
        ax = fig.axes[0]
        bbox = ax.get_position()
        x_pos = bbox.x0  # Borda esquerda do axes em coordenadas de figura

    fig.text(x_pos, 0.01, footer_text,
             ha='left', va='bottom',
             fontsize=9, color='gray',
             fontproperties=theme.font)
