"""
agora-database - Coleta e consulta de dados economicos brasileiros.

Uso:
    from src import collect, sgs, caged

    # Coleta
    collect('sgs')
    collect('caged', year=2025)

    # Query
    df = sgs.read('selic', start='2020')
    df = caged.read(year=2025, uf=35)

Fontes disponiveis:
    - sgs: Series temporais BCB (Selic, CDI, PTAX, IBC-Br, IGP-M)
    - expectations: Expectativas Focus BCB (IPCA, PIB, Cambio, Selic)
    - caged: Microdados CAGED/MTE (admissoes, desligamentos)
    - ipea: Series agregadas IPEADATA
    - bloomberg: Dados de mercado (requer terminal)
"""

# Collectors
from core.collectors import collect, available_sources, get_status

# Explorers (namespaces de query) - via lazy loading
from core.data import sgs, caged, expectations, ipea, bloomberg

# Classes (para uso avancado)
from core.data import QueryEngine, DataManager

__all__ = [
    # Funcoes principais
    'collect',
    'available_sources',
    'get_status',
    # Namespaces de query
    'sgs',
    'caged',
    'expectations',
    'ipea',
    'bloomberg',
    # Classes
    'QueryEngine',
    'DataManager',
]
