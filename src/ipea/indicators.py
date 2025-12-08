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


# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================


def get_indicator_config(key: str) -> dict:
    """
    Retorna configuracao de um indicador.

    Args:
        key: Chave do indicador (ex: 'caged_saldo')

    Returns:
        Dict com code, name, frequency, description, unit, source

    Raises:
        KeyError se indicador nao encontrado
    """
    if key not in IPEA_CONFIG:
        available = ", ".join(IPEA_CONFIG.keys())
        raise KeyError(
            f"Indicador '{key}' nao encontrado. Disponiveis: {available}"
        )
    return IPEA_CONFIG[key]


def list_indicators() -> list[str]:
    """Retorna lista de chaves de indicadores disponiveis."""
    return list(IPEA_CONFIG.keys())


def get_by_frequency(frequency: str) -> dict:
    """
    Retorna indicadores filtrados por frequencia.

    Args:
        frequency: 'daily', 'monthly' ou 'quarterly'

    Returns:
        Dict com indicadores da frequencia especificada
    """
    return {
        key: config
        for key, config in IPEA_CONFIG.items()
        if config["frequency"] == frequency
    }


def get_indicator_keys(frequency: str = None) -> list[str]:
    """
    Retorna lista de chaves de indicadores.

    Args:
        frequency: Filtrar por frequencia (opcional)

    Returns:
        Lista de chaves
    """
    if frequency is None:
        return list(IPEA_CONFIG.keys())
    return [
        key for key, config in IPEA_CONFIG.items()
        if config["frequency"] == frequency
    ]
