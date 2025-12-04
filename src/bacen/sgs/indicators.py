# SGS Codes - Sistema Gerenciador de Series Temporais do BCB

# Configuracao completa de indicadores com metadata
INDICATORS = {
    'ibc_br_bruto': {
        'code': 24363,
        'name': 'IBC-Br Bruto',
        'frequency': 'monthly',
        'description': 'Indice de Atividade Economica do Banco Central - Bruto',
    },
    'ibc_br_dessaz': {
        'code': 24364,
        'name': 'IBC-Br Dessazonalizado',
        'frequency': 'monthly',
        'description': 'Indice de Atividade Economica do Banco Central - Dessazonalizado',
    },
    'igp_m': {
        'code': 189,
        'name': 'IGP-M',
        'frequency': 'monthly',
        'description': 'Indice Geral de Precos do Mercado - Variacao Mensal',
    },
    'selic': {
        'code': 432,
        'name': 'Meta Selic',
        'frequency': 'daily',
        'description': 'Taxa basica de juros da economia brasileira',
    },
    'dolar_ptax': {
        'code': 10813,
        'name': 'Dolar PTAX',
        'frequency': 'daily',
        'description': 'Taxa de cambio Dolar/Real - PTAX Venda',
    },
    'euro_ptax': {
        'code': 21619,
        'name': 'Euro PTAX',
        'frequency': 'daily',
        'description': 'Taxa de cambio Euro/Real - PTAX Venda',
    },
    'cdi': {
        'code': 12,
        'name': 'CDI',
        'frequency': 'daily',
        'description': 'Certificado de Deposito Interbancario - Taxa Diaria',
    },
}


def get_by_frequency(frequency: str) -> dict:
    """Retorna indicadores filtrados por frequencia (daily ou monthly)."""
    return {
        key: config
        for key, config in INDICATORS.items()
        if config['frequency'] == frequency
    }


def get_codes_dict(indicators: dict = None) -> dict[str, int]:
    """
    Retorna dicionario {name: code} no formato esperado por bcb.sgs.get().

    Args:
        indicators: Dict de indicadores (default: todos)

    Returns:
        Dict no formato {'Nome Indicador': codigo_sgs}
    """
    if indicators is None:
        indicators = INDICATORS
    return {config['name']: config['code'] for config in indicators.values()}


def get_indicator_keys(frequency: str = None) -> list[str]:
    """Retorna lista de chaves de indicadores, opcionalmente filtrada por frequencia."""
    if frequency is None:
        return list(INDICATORS.keys())
    return [key for key, config in INDICATORS.items() if config['frequency'] == frequency]


def get_indicator_config(key: str) -> dict:
    """
    Retorna configuracao de um indicador.

    Args:
        key: Chave do indicador (ex: 'selic', 'dolar_ptax')

    Returns:
        Dict com code, name, frequency, description

    Raises:
        KeyError se indicador nao encontrado
    """
    if key not in INDICATORS:
        raise KeyError(f"Indicador '{key}' nao encontrado em INDICATORS")
    return INDICATORS[key]


def list_indicators() -> list[str]:
    """Retorna lista de chaves de indicadores disponiveis."""
    return list(INDICATORS.keys())


# =============================================================================
# Compatibilidade com formato antigo (para imports existentes)
# =============================================================================

IBC_BR = {
    'ibc_br_bruto': 24363,
    'ibc_br_dessaz': 24364,
}

IGP_M = {
    'igp_m': 189,
}

SELIC = {
    'selic': 432,
}

CURRENCY = {
    'dolar_ptax': 10813,
    'euro_ptax': 21619,
}

CDI = {
    'cdi': 12,
}

MONTHLY_INDICATORS = {
    **IBC_BR,
    **IGP_M,
}

DAILY_INDICATORS = {
    **SELIC,
    **CURRENCY,
    **CDI,
}

ALL_SGS_CODES = {
    **MONTHLY_INDICATORS,
    **DAILY_INDICATORS,
}
