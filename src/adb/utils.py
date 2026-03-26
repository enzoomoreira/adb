"""
Utilitarios para manipulacao de datas.

Funcoes comuns usadas pelos explorers para parsing e formatacao.
"""

import pandas as pd


# Colunas de data reconhecidas (ordem de prioridade)
# normalize_date_index() usa esta lista para converter qualquer variante para 'date'
# Dados salvos via DataManager.save() SEMPRE terao coluna 'date' (Schema on Write)
DATE_COLUMNS = ["date", "Date", "data", "Data", "DATE"]


def parse_date(date: str) -> str:
    """
    Normaliza formato de data para YYYY-MM-DD.

    Aceita formatos:
    - '2020' -> '2020-01-01'
    - '2020-01' -> '2020-01-01'
    - '2020-01-15' -> '2020-01-15'

    Args:
        date: Data em formato parcial ou completo

    Returns:
        Data no formato 'YYYY-MM-DD'

    Examples:
        >>> parse_date('2020')
        '2020-01-01'
        >>> parse_date('2020-06')
        '2020-06-01'
        >>> parse_date('2020-06-15')
        '2020-06-15'
    """
    if len(date) == 4:
        return f"{date}-01-01"
    elif len(date) == 7:
        return f"{date}-01"
    return date


def normalize_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza indice datetime de um DataFrame.

    Garante formato consistente:
    - Indice datetime com nome 'date'
    - Colunas de data movidas para indice

    Args:
        df: DataFrame para normalizar

    Returns:
        DataFrame com indice padronizado (ou inalterado se nao tem data)
    """
    if df.empty:
        return df

    # Caso 1: Ja tem DatetimeIndex - so padronizar nome e remover hora
    if pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = df.index.normalize()
        df.index.name = "date"
        return df

    # Caso 2: Tem coluna de data - mover para indice e remover hora
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
            df = df.set_index(col)
            df.index = df.index.normalize()
            df.index.name = "date"
            return df

    # Caso 3: Sem coluna de data reconhecida - retorna como esta
    return df
