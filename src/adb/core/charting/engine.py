import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from .config import CHARTS_PATH
from .styling import theme, currency_formatter, percent_formatter, human_readable_formatter
from .components import add_footer
from .plots.line import plot_line
from .plots.bar import plot_bar

class AgoraPlotter:
    """
    Factory de visualizacao financeira padronizada.
    Orquestra temas, formatadores e componentes.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._fig = None
        self._ax = None
        
    # =========================================================================
    # API Publica
    # =========================================================================

    def plot(
        self,
        x: str = None,
        y: str | list[str] = None,
        kind: str = 'line',
        title: str = None,
        units: str = None,
        source: str = None,
        highlight_last: bool = False,
        y_origin: str = 'zero',
        save_path: str = None,
        **kwargs
    ):
        """
        Gera um grafico padronizado.

        Args:
            x: Coluna para eixo X (default: index)
            y: Coluna(s) para eixo Y (default: todas numericas)
            kind: Tipo de grafico ('line' ou 'bar')
            title: Titulo do grafico
            units: Formatacao do eixo Y ('BRL', 'USD', '%', 'points', 'human')
            source: Fonte dos dados para rodape (ex: 'BCB', 'IBGE')
            highlight_last: Se True, destaca o ultimo valor da serie (apenas line)
            y_origin: Origem do eixo Y para barras ('zero', 'auto'). Default 'zero'.
            save_path: Caminho para salvar o grafico
            **kwargs: Argumentos extras para matplotlib

        Returns:
            matplotlib Axes
        """
        # 1. Setup inicial (Style)
        theme.apply()
        fig, ax = plt.subplots(figsize=(10, 6))
        self._fig = fig
        self._ax = ax
        
        # 2. Resolução de dados
        x_data = self.df.index if x is None else self.df[x]
        
        if y is None:
            y_data = self.df.select_dtypes(include=['number'])
        else:
            y_data = self.df[y]
            
        # 3. Plotagem Core
        if kind == 'line':
            plot_line(ax, x_data, y_data, highlight_last, **kwargs)
        elif kind == 'bar':
            plot_bar(ax, x_data, y_data, y_origin=y_origin, **kwargs)
        else:
            raise ValueError(f"Chart type '{kind}' not supported.")
            
        # 4. Aplicacao de Componentes e Formatacao
        self._apply_formatting(ax, title, units)
        self._apply_decorations(fig, source)
        
        # 5. Output
        if save_path:
            self.save(save_path)
            
        return ax

    # =========================================================================
    # Helpers de Decoracao
    # =========================================================================

    def _apply_formatting(self, ax, title, units):
        # Titulo centralizado
        if title:
            ax.set_title(title, loc='center', pad=20, fontproperties=theme.font, size=18, color=theme.colors.text, weight='bold')
            
        # Formatador Eixo Y
        if units:
            if units == 'BRL':
                ax.yaxis.set_major_formatter(currency_formatter('BRL'))
            elif units == 'USD':
                ax.yaxis.set_major_formatter(currency_formatter('USD'))
            elif units == '%':
                ax.yaxis.set_major_formatter(percent_formatter())
            elif units == 'human':
                ax.yaxis.set_major_formatter(human_readable_formatter())
            # 'points' usa o default (scalar)

    def _apply_decorations(self, fig, source):
        add_footer(fig, source)

    # =========================================================================
    # IO e Exportacao
    # =========================================================================

    def save(self, path: str, dpi: int = 300):
        """
        Salva o grafico atual em arquivo.

        Args:
            path: Caminho do arquivo (ex: 'grafico.png')
            dpi: Resolucao em DPI (default: 300)

        Raises:
            RuntimeError: Se nenhum grafico foi gerado ainda
        """
        if self._fig is None:
            raise RuntimeError("Nenhum grafico gerado. Chame plot() primeiro.")

        # Resolve path
        path_obj = Path(path)
        if not path_obj.is_absolute():
            CHARTS_PATH.mkdir(parents=True, exist_ok=True)
            path_obj = CHARTS_PATH / path_obj

        self._fig.savefig(path_obj, bbox_inches='tight', dpi=dpi)
