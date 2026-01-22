import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional

from .config import CHARTS_PATH

from .theme import theme
from .formatters import currency_formatter, percent_formatter, human_readable_formatter
from .components import add_footer, highlight_last_point


class AgoraPlotter:
    """
    Factory de visualizacao financeira padronizada.
    Orquestra temas, formatadores e componentes.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._fig = None
        self._ax = None
        
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
            self._plot_line(ax, x_data, y_data, highlight_last, **kwargs)
        elif kind == 'bar':
            self._plot_bar(ax, x_data, y_data, y_origin=y_origin, **kwargs)
        else:
            raise ValueError(f"Chart type '{kind}' not supported.")
            
        # 4. Aplicacao de Componentes e Formatacao
        self._apply_formatting(ax, title, units)
        self._apply_decorations(fig, source)
        
        # 5. Output
        if save_path:
            self.save(save_path)
            
        return ax

    def _plot_line(self, ax, x, y_data, highlight, **kwargs):
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

    def _plot_bar(self, ax, x, y_data, y_origin: str = 'zero', **kwargs):
        if 'color' not in kwargs:
            kwargs['color'] = theme.colors.primary

        # Largura da barra inteligente baseada na frequencia dos dados
        width = 0.8
        if pd.api.types.is_datetime64_any_dtype(x):
            if len(x) > 1:
                avg_diff = (x.max() - x.min()) / (len(x) - 1)
                if avg_diff.days > 25:
                    width = 20  # Mensal
                elif avg_diff.days > 300:
                    width = 300  # Anual

        if isinstance(y_data, pd.DataFrame):
            if y_data.shape[1] > 1:
                # Multiplas series: usa pandas plot
                y_data.plot(kind='bar', ax=ax, width=0.8, **kwargs)
                return
            else:
                vals = y_data.iloc[:, 0]
        else:
            vals = y_data

        ax.bar(x, vals, width=width, **kwargs)

        # Ajusta origem do eixo Y
        if y_origin == 'auto':
            # Ajusta eixo Y para focar nos dados com margem
            vals_clean = vals.dropna()
            if not vals_clean.empty:
                ymin, ymax = vals_clean.min(), vals_clean.max()
                margin = (ymax - ymin) * 0.1  # 10% de margem
                ax.set_ylim(ymin - margin, ymax + margin)
        else:
            # Default: inclui zero no eixo Y
            ymin, ymax = ax.get_ylim()
            if ymin > 0:
                ax.set_ylim(0, ymax)
            elif ymax < 0:
                ax.set_ylim(ymin, 0)

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
