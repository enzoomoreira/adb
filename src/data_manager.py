from pathlib import Path
import pandas as pd
from datetime import datetime


class DataManager:
    """Gerenciador de dados Parquet para indicadores do BCB"""

    def __init__(self, base_path: Path):
        """
        Inicializa o gerenciador de dados.

        Args:
            base_path: Caminho base para diretório data/
        """
        self.base_path = base_path
        self.raw_path = base_path / 'raw'
        self.processed_path = base_path / 'processed'

    def save_indicator(self, df: pd.DataFrame, indicator_key: str,
                      frequency: str, metadata: dict = None):
        """
        Salva DataFrame de um indicador com metadata.

        Args:
            df: DataFrame com dados do indicador (index: date, coluna: value)
            indicator_key: Identificador único do indicador (ex: 'dolar_ptax')
            frequency: Frequência dos dados ('daily' ou 'monthly')
            metadata: Dicionário com metadata adicional (opcional)
        """
        file_path = self._get_file_path(indicator_key, frequency)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Adicionar metadata ao DataFrame
        df.attrs['indicator_key'] = indicator_key
        df.attrs['frequency'] = frequency
        df.attrs['created_at'] = datetime.now().isoformat()
        df.attrs['last_update'] = datetime.now().isoformat()
        if metadata:
            df.attrs.update(metadata)

        # Salvar Parquet com compressão
        df.to_parquet(file_path, engine='pyarrow',
                     compression='snappy', index=True)

    def read_indicator(self, indicator_key: str, frequency: str) -> pd.DataFrame:
        """
        Lê dados de um indicador.

        Args:
            indicator_key: Identificador único do indicador
            frequency: Frequência dos dados ('daily' ou 'monthly')

        Returns:
            DataFrame com dados do indicador (vazio se não existir)
        """
        file_path = self._get_file_path(indicator_key, frequency)
        if not file_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(file_path, engine='pyarrow')

    def append_indicator(self, new_df: pd.DataFrame, indicator_key: str,
                        frequency: str):
        """
        Adiciona novos dados a um indicador existente (update incremental).

        Args:
            new_df: DataFrame com novos dados
            indicator_key: Identificador único do indicador
            frequency: Frequência dos dados ('daily' ou 'monthly')
        """
        existing_df = self.read_indicator(indicator_key, frequency)

        if existing_df.empty:
            # Se não existe, salvar como novo
            self.save_indicator(new_df, indicator_key, frequency)
            return

        # Concatenar e remover duplicatas (manter mais recente)
        combined = pd.concat([existing_df, new_df])
        combined = combined[~combined.index.duplicated(keep='last')]
        combined = combined.sort_index()

        # Atualizar metadata
        combined.attrs = existing_df.attrs.copy()
        combined.attrs['last_update'] = datetime.now().isoformat()

        # Salvar arquivo atualizado
        file_path = self._get_file_path(indicator_key, frequency)
        combined.to_parquet(file_path, engine='pyarrow',
                          compression='snappy', index=True)

    def get_last_date(self, indicator_key: str, frequency: str):
        """
        Retorna a última data disponível para um indicador.

        Args:
            indicator_key: Identificador único do indicador
            frequency: Frequência dos dados ('daily' ou 'monthly')

        Returns:
            datetime da última data ou None se não existir
        """
        df = self.read_indicator(indicator_key, frequency)
        if df.empty:
            return None
        return df.index.max()

    def consolidate_monthly(self) -> pd.DataFrame:
        """
        Consolida todos os indicadores mensais em um DataFrame.

        Returns:
            DataFrame com todos os indicadores mensais (formato wide)
        """
        monthly_path = self.raw_path / 'monthly'
        if not monthly_path.exists():
            return pd.DataFrame()

        dfs = []
        for file in monthly_path.glob('*.parquet'):
            df = pd.read_parquet(file)
            indicator_name = df.attrs.get('indicator_key', file.stem)
            df = df.rename(columns={'value': indicator_name})
            dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        # Merge all DataFrames (outer join)
        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how='outer')

        return result.sort_index()

    def consolidate_daily(self) -> pd.DataFrame:
        """
        Consolida todos os indicadores diários em um DataFrame.

        Returns:
            DataFrame com todos os indicadores diários (formato wide)
        """
        daily_path = self.raw_path / 'daily'
        if not daily_path.exists():
            return pd.DataFrame()

        dfs = []
        for file in daily_path.glob('*.parquet'):
            df = pd.read_parquet(file)
            indicator_name = df.attrs.get('indicator_key', file.stem)
            df = df.rename(columns={'value': indicator_name})
            dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        # Merge all DataFrames (outer join)
        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, how='outer')

        return result.sort_index()

    def _get_file_path(self, indicator_key: str, frequency: str) -> Path:
        """
        Retorna o caminho do arquivo para um indicador.

        Args:
            indicator_key: Identificador único do indicador
            frequency: Frequência dos dados ('daily' ou 'monthly')

        Returns:
            Path do arquivo Parquet
        """
        return self.raw_path / frequency / f"{indicator_key}.parquet"
