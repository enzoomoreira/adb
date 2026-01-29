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
    "selic_acum_mensal": {
        "code": 4390,
        "name": "Selic Acumulada no Mes",
        "frequency": "monthly",
        "description": "Taxa de juros acumulada no mes",
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
    # IBC-BR Setorial (lancado abril/2025)
    "ibc_br_agro": {
        "code": 29602,
        "name": "IBC-Br Agropecuaria",
        "frequency": "monthly",
        "description": "IBC-Br Setor Agropecuario - Dessazonalizado",
    },
    "ibc_br_industria": {
        "code": 29604,
        "name": "IBC-Br Industria",
        "frequency": "monthly",
        "description": "IBC-Br Setor Industrial - Dessazonalizado",
    },
    "ibc_br_servicos": {
        "code": 29606,
        "name": "IBC-Br Servicos",
        "frequency": "monthly",
        "description": "IBC-Br Setor de Servicos - Dessazonalizado",
    },
}
