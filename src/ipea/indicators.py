"""
Configuracao de indicadores IPEA disponiveis.

Series temporais agregadas do IPEADATA.
"""

# =============================================================================
# CONFIGURACAO DE INDICADORES IPEA
# =============================================================================

IPEA_CONFIG = {
    # === CAGED AGREGADO (Series Mensais) ===
    "caged_saldo": {
        "code": "CAGED12_SALDON12",
        "name": "Saldo do Novo CAGED",
        "frequency": "monthly",
        "description": "Saldo de empregos formais (admissoes - desligamentos)",
        "unit": "pessoas",
        "source": "MTE/CAGED",
    },
    "caged_admissoes": {
        "code": "CAGED12_ADMISN12",
        "name": "Admissoes CAGED",
        "frequency": "monthly",
        "description": "Total de admissoes no Novo CAGED",
        "unit": "pessoas",
        "source": "MTE/CAGED",
    },
    "caged_desligamentos": {
        "code": "CAGED12_DESLIGN12",
        "name": "Desligamentos CAGED",
        "frequency": "monthly",
        "description": "Total de desligamentos no Novo CAGED",
        "unit": "pessoas",
        "source": "MTE/CAGED",
    },
    # === DESEMPREGO (PNAD) ===
    "taxa_desemprego": {
        "code": "PNADC12_TDESOC12",
        "name": "Taxa de Desocupacao",
        "frequency": "monthly",
        "description": "Taxa de desocupacao - PNAD Continua",
        "unit": "%",
        "source": "IBGE/PNAD",
    },
}
