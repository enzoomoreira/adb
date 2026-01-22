"""
Funcoes de transformacao para series temporais.

Uso:
    from adb.core.charting import yoy, mom, accum_12m

    df_yoy = yoy(df)           # Variacao ano contra ano
    df_mom = mom(df)           # Variacao mes contra mes
    df_accum = accum_12m(df)   # Acumulado 12 meses
"""

import pandas as pd


def mom(df: pd.DataFrame | pd.Series, periods: int = 1) -> pd.DataFrame | pd.Series:
    """
    Calcula variacao percentual mensal (Month-over-Month).

    Args:
        df: DataFrame ou Series com indice temporal
        periods: Numero de periodos para comparacao (default: 1)

    Returns:
        DataFrame/Series com variacao percentual

    Example:
        >>> df_mom = mom(df)  # Variacao mensal em %
    """
    return df.pct_change(periods=periods) * 100


def yoy(df: pd.DataFrame | pd.Series, periods: int = 12) -> pd.DataFrame | pd.Series:
    """
    Calcula variacao percentual anual (Year-over-Year).

    Assume dados mensais por default (12 periodos = 1 ano).

    Args:
        df: DataFrame ou Series com indice temporal
        periods: Numero de periodos para comparacao (default: 12 para mensal)

    Returns:
        DataFrame/Series com variacao percentual

    Example:
        >>> df_yoy = yoy(df)          # YoY para dados mensais
        >>> df_yoy = yoy(df, periods=4)  # YoY para dados trimestrais
    """
    return df.pct_change(periods=periods) * 100


def accum_12m(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """
    Calcula variacao acumulada em 12 meses.

    Util para indices de inflacao mensal (ex: IPCA mensal -> IPCA 12m).
    Formula: (Produto(1 + x/100) - 1) * 100

    Args:
        df: DataFrame ou Series com variacoes mensais em %

    Returns:
        DataFrame/Series com variacao acumulada 12 meses

    Example:
        >>> ipca_mensal = sidra.read('ipca')
        >>> ipca_12m = accum_12m(ipca_mensal)
    """
    def _calc_accum(x):
        return ((1 + x / 100).prod() - 1) * 100

    return df.rolling(12).apply(_calc_accum, raw=False)


def diff(df: pd.DataFrame | pd.Series, periods: int = 1) -> pd.DataFrame | pd.Series:
    """
    Calcula diferenca absoluta entre periodos.

    Args:
        df: DataFrame ou Series com indice temporal
        periods: Numero de periodos para diferenca (default: 1)

    Returns:
        DataFrame/Series com diferenca

    Example:
        >>> df_diff = diff(df)  # Diferenca para periodo anterior
    """
    return df.diff(periods=periods)


def normalize(
    df: pd.DataFrame | pd.Series,
    base: int = 100,
    base_date: str = None
) -> pd.DataFrame | pd.Series:
    """
    Normaliza serie para um valor base em uma data especifica.

    Util para comparar series com escalas diferentes.

    Args:
        df: DataFrame ou Series com indice temporal
        base: Valor base para normalizacao (default: 100)
        base_date: Data base para normalizacao. Se None, usa primeira data.

    Returns:
        DataFrame/Series normalizada

    Example:
        >>> df_norm = normalize(df)  # Base 100 na primeira data
        >>> df_norm = normalize(df, base_date='2020-01-01')  # Base 100 em 2020
    """
    if base_date is not None:
        base_date = pd.Timestamp(base_date)
        base_value = df.loc[base_date]
    else:
        base_value = df.iloc[0]

    return (df / base_value) * base
