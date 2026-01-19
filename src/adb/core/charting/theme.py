import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
import os

# Caminho para assets dentro do pacote charting
ASSETS_PATH = Path(__file__).parent / 'assets'
FONT_PATH = ASSETS_PATH / 'fonts' / 'BradescoSans-Light.ttf'

# Cores
COLORS = {
    "primary": "#00464D",  # Cor original do legacy
    "axis": "#00464D",
    "grid": "lightgray",
    "background": "white",
    "text": "#00464D"
}

def load_fonts():
    """Carrega fontes personalizadas."""
    if FONT_PATH.exists():
        fm.fontManager.addfont(str(FONT_PATH))
        return fm.FontProperties(fname=str(FONT_PATH))
    return None

def apply_style():
    """Aplica o estilo padrao do Agora."""
    font_prop = load_fonts()
    font_name = font_prop.get_name() if font_prop else "Sans Serif"
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Customizacoes globais
    rc_params = {
        'font.family': font_name,
        'text.color': COLORS['text'],
        'axes.labelcolor': COLORS['text'],
        'xtick.color': COLORS['text'],
        'ytick.color': COLORS['text'],
        'axes.edgecolor': COLORS['grid'],
        'grid.color': COLORS['grid'],
        'grid.linestyle': '-',
        'grid.linewidth': 0.8,
        'figure.figsize': (10, 6),
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.spines.left': False, # Legacy removia box, vamos manter minimalista
        'axes.spines.bottom': True,
    }
    
    plt.rcParams.update(rc_params)
    return font_prop
