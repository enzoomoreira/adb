"""
Modulo de interface com usuario (display, formatacao).

Separado de core para permitir uso headless da biblioteca.
"""

from adb.ui.display import Display, get_display

__all__ = ["Display", "get_display"]
