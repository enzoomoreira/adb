# SGS Codes - Sistema Gerenciador de Series Temporais do BCB

# Configuracao de indicadores SGS
SGS_CONFIG = {
    "ibc_br_bruto": {
        "code": 24363,
        "name": "IBC-Br Bruto",
        "frequency": "monthly",
        "description": "Indice de Atividade Economica do Banco Central - Bruto",
    },
    "ibc_br_dessaz": {
        "code": 24364,
        "name": "IBC-Br Dessazonalizado",
        "frequency": "monthly",
        "description": "Indice de Atividade Economica do Banco Central - Dessazonalizado",
    },
    "igp_m": {
        "code": 189,
        "name": "IGP-M",
        "frequency": "monthly",
        "description": "Indice Geral de Precos do Mercado - Variacao Mensal",
    },
    "selic": {
        "code": 432,
        "name": "Meta Selic",
        "frequency": "daily",
        "description": "Taxa basica de juros da economia brasileira",
    },
    "dolar_ptax": {
        "code": 10813,
        "name": "Dolar PTAX",
        "frequency": "daily",
        "description": "Taxa de cambio Dolar/Real - PTAX Venda",
    },
    "euro_ptax": {
        "code": 21619,
        "name": "Euro PTAX",
        "frequency": "daily",
        "description": "Taxa de cambio Euro/Real - PTAX Venda",
    },
    "cdi": {
        "code": 12,
        "name": "CDI",
        "frequency": "daily",
        "description": "Certificado de Deposito Interbancario - Taxa Diaria",
    },
}


def get_by_frequency(frequency: str) -> dict:
    """Retorna indicadores filtrados por frequencia (daily ou monthly)."""
    return {
        key: config
        for key, config in SGS_CONFIG.items()
        if config["frequency"] == frequency
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
        indicators = SGS_CONFIG
    return {config["name"]: config["code"] for config in indicators.values()}


def get_indicator_keys(frequency: str = None) -> list[str]:
    """Retorna lista de chaves de indicadores, opcionalmente filtrada por frequencia."""
    if frequency is None:
        return list(SGS_CONFIG.keys())
    return [
        key for key, config in SGS_CONFIG.items() if config["frequency"] == frequency
    ]


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
    if key not in SGS_CONFIG:
        raise KeyError(f"Indicador '{key}' nao encontrado em SGS_CONFIG")
    return SGS_CONFIG[key]


def list_indicators() -> list[str]:
    """Retorna lista de chaves de indicadores disponiveis."""
    return list(SGS_CONFIG.keys())
