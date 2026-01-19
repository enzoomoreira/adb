import pandas as pd
from .plotter import AgoraPlotter

@pd.api.extensions.register_dataframe_accessor("agora")
class AgoraAccessor:
    """
    Pandas Accessor para funcionalidade de charting.
    Uso: df.agora.plot()
    """
    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj
        self._plotter = None

    @staticmethod
    def _validate(obj):
        # Validacoes se necessario
        pass

    @property
    def plotter(self):
        if self._plotter is None:
            self._plotter = AgoraPlotter(self._obj)
        return self._plotter

    def plot(self, kind='line', title=None, save_path=None, **kwargs):
        """
        Cria um grafico estilo Agora-Database.
        
        Args:
            kind: 'line' ou 'bar'
            title: Titulo do grafico (opcional)
            save_path: Se fornecido, salva o grafico neste caminho
            **kwargs: Argumentos extras passados para matplotlib
        """
        return self.plotter.plot(kind=kind, title=title, save_path=save_path, **kwargs)
        
    def save(self, path):
        """Salva o grafico atual (se existir)."""
        if self._plotter:
            self._plotter.save(path)
        else:
             raise RuntimeError("Nenhum grafico gerado ainda. Chame .plot() primeiro.")

