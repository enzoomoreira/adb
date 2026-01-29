import pandas as pd
from .engine import AgoraPlotter

@pd.api.extensions.register_dataframe_accessor("agora")
class AgoraAccessor:
    """
    Pandas Accessor para funcionalidade de charting.
    Uso: df.agora.plot()
    """
    def __init__(self, pandas_obj):
        self._obj = pandas_obj
        self._plotter = None

    @property
    def plotter(self):
        if self._plotter is None:
            self._plotter = AgoraPlotter(self._obj)
        return self._plotter

    def plot(
        self,
        kind: str = 'line',
        title: str = None,
        save_path: str = None,
        moving_avg: int = None,
        show_ath: bool = False,
        show_atl: bool = False,
        overlays: dict = None,
        **kwargs
    ):
        """
        Cria um grafico estilo Agora-Database.

        Args:
            kind: 'line' ou 'bar'
            title: Titulo do grafico (opcional)
            save_path: Se fornecido, salva o grafico neste caminho
            moving_avg: Janela da media movel (ex: 12 para MM12)
            show_ath: Se True, mostra linha no All-Time High
            show_atl: Se True, mostra linha no All-Time Low
            overlays: Dicionario com overlays customizados:
                - 'hlines': Lista de dicts com {value, label, color, linestyle}
                - 'band': Dict com {lower, upper, color, alpha, label}
            **kwargs: Argumentos extras passados para matplotlib
        """
        return self.plotter.plot(
            kind=kind,
            title=title,
            save_path=save_path,
            moving_avg=moving_avg,
            show_ath=show_ath,
            show_atl=show_atl,
            overlays=overlays,
            **kwargs
        )
        
    def save(self, path):
        """Salva o grafico atual (se existir)."""
        if self._plotter:
            self._plotter.save(path)
        else:
            raise RuntimeError("Nenhum grafico gerado ainda. Chame .plot() primeiro.")
