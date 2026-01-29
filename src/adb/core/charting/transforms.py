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


def annualize_daily(
    df: pd.DataFrame | pd.Series,
    trading_days: int = 252
) -> pd.DataFrame | pd.Series:
    """
    Anualiza taxa diaria para taxa anual usando juros compostos.

    Formula: ((1 + r_diaria) ^ dias_uteis - 1) * 100

    Args:
        df: DataFrame ou Series com taxas diarias em %
        trading_days: Dias uteis no ano (default: 252 para Brasil)

    Returns:
        DataFrame/Series com taxas anualizadas em %

    Example:
        >>> cdi_diario = sgs.read('cdi')  # Taxa diaria em %
        >>> cdi_anual = annualize_daily(cdi_diario)
    """
    # Converte % para decimal, aplica formula, retorna em %
    rate_decimal = df / 100
    annualized = (1 + rate_decimal) ** trading_days - 1
    return annualized * 100


def compound_rolling(
    df: pd.DataFrame | pd.Series,
    window: int = 12
) -> pd.DataFrame | pd.Series:
    """
    Calcula retorno composto em janela movel.

    Multiplica os fatores (1 + taxa) ao longo da janela.
    Util para calcular Selic acumulada 12 meses a partir de taxas mensais.

    Args:
        df: DataFrame ou Series com taxas em % (ex: Selic mensal)
        window: Tamanho da janela em periodos (default: 12 meses)

    Returns:
        DataFrame/Series com retorno composto em %

    Example:
        >>> selic_mensal = sgs.read('selic_acumm_mensal')
        >>> selic_12m = compound_rolling(selic_mensal)
    """
    # Converte % para fator, aplica produto rolling, retorna em %
    factor = 1 + (df / 100)

    def _rolling_prod(x):
        return x.prod()

    compounded = factor.rolling(window).apply(_rolling_prod, raw=True) - 1
    return compounded * 100


def real_rate(
    nominal: pd.DataFrame | pd.Series,
    inflation: pd.DataFrame | pd.Series
) -> pd.DataFrame | pd.Series:
    """
    Calcula taxa de juros real usando a Equacao de Fisher.

    Formula exata: ((1 + nominal) / (1 + inflacao) - 1) * 100

    Args:
        nominal: Taxa nominal em % (ex: Selic 12m)
        inflation: Taxa de inflacao em % (ex: IPCA 12m)

    Returns:
        DataFrame/Series com taxa real em %

    Example:
        >>> selic_12m = compound_rolling(sgs.read('selic_acumm_mensal'))
        >>> ipca_12m = sidra.read('ipca_12m')
        >>> juros_real = real_rate(selic_12m, ipca_12m)
    """
    # Converte % para decimal
    nominal_dec = nominal / 100
    inflation_dec = inflation / 100

    # Equacao de Fisher exata
    real = (1 + nominal_dec) / (1 + inflation_dec) - 1
    return real * 100


def to_month_end(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """
    Normaliza indice temporal para fim do mes.

    Util para alinhar series com frequencias diferentes antes de operacoes.

    Args:
        df: DataFrame ou Series com DatetimeIndex

    Returns:
        DataFrame/Series com indice normalizado para fim do mes

    Example:
        >>> selic = sgs.read('selic')
        >>> selic_me = to_month_end(selic)  # Indice no ultimo dia do mes
    """
    result = df.copy()
    result.index = result.index.to_period("M").to_timestamp("M")
    return result
