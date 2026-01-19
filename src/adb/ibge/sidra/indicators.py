# SIDRA Config - IBGE

# Configuracao de indicadores IBGE Sidra
SIDRA_CONFIG = {
    "ipca": {
        "code": 1737, # Tabela 1737
        "name": "IPCA",
        "frequency": "monthly",
        "parameters": {
            "agregados": "1737",
            "periodos": "all",
            "variaveis": "63", # IPCA - Variacao mensal (63), acumulada no ano (69), acumulada 12 meses (2265)
            "nivel_territorial": "1", # N1 - Brasil
            "localidades": "all",
        },
        "description": "Indice Nacional de Precos ao Consumidor Amplo",
    },
    "ipca_12m": {
        "code": 1737,
        "name": "IPCA - 12 meses",
        "frequency": "monthly",
        "parameters": {
            "agregados": "1737",
            "periodos": "all",
            "variaveis": "2265",
            "nivel_territorial": "1",
            "localidades": "all",
        },
        "description": "IPCA - Variacao acumulada em 12 meses",
    },
    "pib": {
        "code": 1620,
        "name": "PIB Trimestral",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "1620",
            "periodos": "all",
            "variaveis": "583", # Serie encadeada do indice de volume
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11255[90707]", # PIB a precos de mercado
            "frequency": "quarterly",
        },
        "description": "Produto Interno Bruto - Trimestral (Serie Encadeada)",
    },
    "pim": {
        "code": 8888,
        "name": "PIM - Industria Geral",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8888", # Substitui 8159
            "periodos": "all",
            "variaveis": "12606", # Numero-indice
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "544[129314]", # 1 Industria geral
        },
        "description": "Producao Industrial Mensal - Industria Geral",
    },
    "pmc_varejo": {
        "code": 8880,
        "name": "PMC - Varejo",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8880", # Substitui 8184
            "periodos": "all",
            "variaveis": "7169", # Volume de Vendas
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56734]", # Indice de volume
        },
        "description": "Pesquisa Mensal de Comercio - Varejo (Volume)",
    },
    "pmc_ampliado": {
        "code": 8881,
        "name": "PMC - Varejo Ampliado",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8881", # Substitui 8185
            "periodos": "all",
            "variaveis": "7169", # Volume de Vendas
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56736]", # Indice de volume ampliado
        },
        "description": "Pesquisa Mensal de Comercio - Varejo Ampliado (Volume)",
    },
    "pms": {
        "code": 5906,
        "name": "PMS - Servicos",
        "frequency": "monthly",
        "parameters": {
            "agregados": "5906", # Substitui 8161
            "periodos": "all",
            "variaveis": "7167", # Volume de Servicos
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56726]", # Indice de volume
        },
        "description": "Pesquisa Mensal de Servicos - Volume",
    },
    "ipca_grupos": {
        "code": 7060,
        "name": "IPCA - Grupos",
        "frequency": "monthly",
        "parameters": {
            "agregados": "7060",
            "periodos": "all",
            "variaveis": "63", # Variacao mensal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "315[all]", # Todos os grupos
        },
        "description": "IPCA - Variacao Mensal por Grupos",
    },
    "pnad_desocupacao": {
        "code": 4099,
        "name": "Taxa de Desocupacao (PNAD)",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "4099",
            "periodos": "all",
            "variaveis": "4099", # Taxa de desocupacao
            "nivel_territorial": "1",
            "localidades": "all",
            "frequency": "quarterly",
        },
        "description": "Taxa de Desocupacao - PNAD Continua",
    }
}
