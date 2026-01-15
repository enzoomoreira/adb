"""
Configuracao dos indicadores CAGED disponiveis.
"""

from datetime import datetime


CAGED_CONFIG = {
    "cagedmov": {
        "prefix": "CAGEDMOV",
        "name": "Movimentacoes",
        "description": "Movimentacoes CAGED (admissoes e desligamentos)",
        "start_year": 2020,
    },
    "cagedfor": {
        "prefix": "CAGEDFOR",
        "name": "Fora do Prazo",
        "description": "Declaracoes CAGED fora do prazo",
        "start_year": 2020,
    },
    "cagedexc": {
        "prefix": "CAGEDEXC",
        "name": "Exclusoes",
        "description": "Exclusoes de movimentacoes CAGED",
        "start_year": 2020,
    },
}


def get_available_periods(start_year: int = 2020, lag_months: int = 2) -> list[tuple[int, int]]:
    """
    Retorna lista de periodos (ano, mes) disponiveis.

    Dados CAGED sao publicados com atraso de ~1-2 meses.

    Args:
        start_year: Ano inicial (default: 2020, inicio do Novo CAGED)
        lag_months: Meses de atraso na publicacao (default: 2)

    Returns:
        Lista de tuplas (ano, mes) desde start_year ate ultimo disponivel
    """
    from dateutil.relativedelta import relativedelta

    periods = []
    now = datetime.now()

    # Ultimo mes disponivel (considerando atraso)
    last_available = now - relativedelta(months=lag_months)

    for year in range(start_year, last_available.year + 1):
        for month in range(1, 13):
            if year == last_available.year and month > last_available.month:
                break
            periods.append((year, month))

    return periods
