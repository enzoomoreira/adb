import matplotlib.font_manager as fm
from pathlib import Path

# Correctly locate assets relative to this module
# src/adb/core/charting/styling/fonts.py -> parent=styling -> parent=charting -> assets
ASSETS_PATH = Path(__file__).parent.parent / 'assets'
FONT_PATH = ASSETS_PATH / 'fonts' / 'BradescoSans-Light.ttf'

def load_font() -> fm.FontProperties:
    """
    Carrega fonte customizada para graficos.

    Returns:
        FontProperties da fonte Bradesco Sans se disponivel,
        caso contrario fallback para sans-serif.
    """
    if FONT_PATH.exists():
        fm.fontManager.addfont(str(FONT_PATH))
        return fm.FontProperties(fname=str(FONT_PATH))
    return fm.FontProperties(family='sans-serif')
