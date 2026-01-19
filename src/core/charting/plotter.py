import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from .theme import apply_style, COLORS

class AgoraPlotter:
    """
    Classe responsavel por gerar graficos padronizados a partir de DataFrames.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.font_prop = apply_style()
        self.fig = None
        self.ax = None
        
    def plot(self, 
             x: str = None, 
             y: str | list[str] = None, 
             kind: str = 'line', 
             title: str = None, 
             save_path: str = None, 
             **kwargs):
        """
        Gera o grafico.
        
        Args:
            x: Coluna para eixo X (se None, usa index)
            y: Coluna(s) para eixo Y (se None, usa todas as numericas)
            kind: 'line' ou 'bar'
            title: Titulo do grafico
            save_path: Caminho para salvar imagem (opcional)
        """
        self.fig, self.ax = plt.subplots()
        
        # Resolver dados
        x_data = self.df.index if x is None else self.df[x]
        
        if y is None:
            # Seleciona colunas numericas se Y nao especificado
            y_data = self.df.select_dtypes(include=['number'])
        else:
            y_data = self.df[y]
            
        # Plotting
        if kind == 'line':
            self._plot_line(x_data, y_data, **kwargs)
        elif kind == 'bar':
            self._plot_bar(x_data, y_data, **kwargs)
        else:
            raise ValueError(f"Tipo de grafico '{kind}' nao suportado.")
            
        # Formatacao
        self._format_axes(title)
        
        if save_path:
            self.save(save_path)
            
        return self.ax
        
    def _plot_line(self, x, y_data, **kwargs):
        """Renderiza grafico de linhas."""
        if isinstance(y_data, pd.Series):
            self.ax.plot(x, y_data, linewidth=2, color=COLORS['primary'], **kwargs)
        else:
            # DataFrame (multiplas linhas)
            for col in y_data.columns:
                self.ax.plot(x, y_data[col], linewidth=2, label=col, **kwargs)
            self.ax.legend()
            
    def _plot_bar(self, x, y_data, **kwargs):
        """Renderiza grafico de barras."""
        if isinstance(y_data, pd.DataFrame) and y_data.shape[1] > 1:
             # Multiplas barras
             y_data.plot(kind='bar', ax=self.ax, width=0.8, color=COLORS['primary'], **kwargs)
        else:
            # Serie unica
            bars = self.ax.bar(x, y_data if isinstance(y_data, pd.Series) else y_data.iloc[:, 0], 
                             width=0.8, color=COLORS['primary'], **kwargs)
            self.ax.bar_label(bars, padding=3, color=COLORS['text'], fmt='%.2f')

    def _format_axes(self, title):
        """Aplica formatacao visual padrao."""
        if title:
            self.ax.set_title(title, pad=20, fontproperties=self.font_prop, size=18, color=COLORS['primary'])
            
        # Eixo Y
        self.ax.tick_params(axis='y', colors='lightgray')
        for label in self.ax.get_yticklabels():
            label.set_fontproperties(self.font_prop)
            label.set_color(COLORS['text'])
            
        # Eixo X
        self.ax.tick_params(axis='x', colors=COLORS['text'])
        for label in self.ax.get_xticklabels():
            label.set_fontproperties(self.font_prop)
            label.set_color(COLORS['text'])
            
        # Formata datas no eixo X se aplicavel
        if isinstance(self.df.index, pd.DatetimeIndex) or pd.api.types.is_datetime64_any_dtype(self.df.index):
             pass # Matplotlib lida bem, mas podemos forcar formataçao BR se precisar

    def save(self, path: str):
        """Salva a figura atual."""
        if self.fig:
            # Garante diretorio
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.fig.savefig(path, bbox_inches='tight', dpi=300)
            print(f"Grafico salvo em: {path}")
