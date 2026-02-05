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
    "ipca_indice": {
        "code": 1737,
        "name": "IPCA - Numero-indice",
        "frequency": "monthly",
        "parameters": {
            "agregados": "1737",
            "periodos": "all",
            "variaveis": "2266",  # Numero-indice (base dez/1993=100)
            "nivel_territorial": "1",
            "localidades": "all",
        },
        "description": "IPCA - Numero-indice (base dez/1993=100)",
    },
    "ipca_3m": {
        "code": 1737,
        "name": "IPCA - 3 meses",
        "frequency": "monthly",
        "parameters": {
            "agregados": "1737",
            "periodos": "all",
            "variaveis": "2263",  # Variacao acumulada 3 meses
            "nivel_territorial": "1",
            "localidades": "all",
        },
        "description": "IPCA - Variacao acumulada em 3 meses",
    },
    "ipca_6m": {
        "code": 1737,
        "name": "IPCA - 6 meses",
        "frequency": "monthly",
        "parameters": {
            "agregados": "1737",
            "periodos": "all",
            "variaveis": "2264",  # Variacao acumulada 6 meses
            "nivel_territorial": "1",
            "localidades": "all",
        },
        "description": "IPCA - Variacao acumulada em 6 meses",
    },
    "ipca_ytd": {
        "code": 1737,
        "name": "IPCA - YTD",
        "frequency": "monthly",
        "parameters": {
            "agregados": "1737",
            "periodos": "all",
            "variaveis": "69",  # Variacao acumulada no ano
            "nivel_territorial": "1",
            "localidades": "all",
        },
        "description": "IPCA - Variacao acumulada no ano",
    },
    "pib": {
        "code": 1620,
        "name": "PIB Trimestral",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "1620",
            "periodos": "all",
            "variaveis": "583",  # Serie encadeada do indice de volume
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11255[90707]",  # PIB a precos de mercado
            "frequency": "quarterly",
        },
        "description": "Produto Interno Bruto - Trimestral (Serie Encadeada)",
    },
    "pib_dessaz": {
        "code": 1621,
        "name": "PIB Trimestral (Dessaz)",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "1621",
            "periodos": "all",
            "variaveis": "584",  # Serie encadeada com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11255[90707]",
            "frequency": "quarterly",
        },
        "description": "PIB Trimestral - Dessazonalizado",
    },
    "pib_yoy": {
        "code": 5932,
        "name": "PIB - Taxa YoY",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "5932",
            "periodos": "all",
            "variaveis": "6561",  # Taxa trimestral YoY
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11255[90707]",
            "frequency": "quarterly",
        },
        "description": "PIB - Taxa YoY (trimestre/mesmo trimestre ano anterior)",
    },
    "pib_4q": {
        "code": 5932,
        "name": "PIB - Taxa 4 trimestres",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "5932",
            "periodos": "all",
            "variaveis": "6562",  # Taxa acumulada 4 trimestres
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11255[90707]",
            "frequency": "quarterly",
        },
        "description": "PIB - Taxa acumulada em 4 trimestres",
    },
    "pib_ytd": {
        "code": 5932,
        "name": "PIB - Taxa YTD",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "5932",
            "periodos": "all",
            "variaveis": "6563",  # Taxa acumulada no ano
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11255[90707]",
            "frequency": "quarterly",
        },
        "description": "PIB - Taxa acumulada no ano",
    },
    "pib_qoq": {
        "code": 5932,
        "name": "PIB - Taxa QoQ",
        "frequency": "quarterly",
        "parameters": {
            "agregados": "5932",
            "periodos": "all",
            "variaveis": "6564",  # Taxa QoQ
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11255[90707]",
            "frequency": "quarterly",
        },
        "description": "PIB - Taxa QoQ (trimestre/trimestre anterior dessaz)",
    },
    "pim": {
        "code": 8888,
        "name": "PIM - Industria Geral",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8888",
            "periodos": "all",
            "variaveis": "12606",  # Numero-indice
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "544[129314]",  # 1 Industria geral
        },
        "description": "Producao Industrial Mensal - Industria Geral",
    },
    "pim_dessaz": {
        "code": 8888,
        "name": "PIM - Industria Geral (Dessaz)",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8888",
            "periodos": "all",
            "variaveis": "12607",  # Numero-indice com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "544[129314]",
        },
        "description": "Producao Industrial Mensal - Dessazonalizado",
    },
    "pim_mom": {
        "code": 8888,
        "name": "PIM - Variacao MoM",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8888",
            "periodos": "all",
            "variaveis": "11601",  # Variacao m/m-1 com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "544[129314]",
        },
        "description": "Producao Industrial Mensal - Variacao m/m-1 (dessaz)",
    },
    "pim_yoy": {
        "code": 8888,
        "name": "PIM - Variacao YoY",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8888",
            "periodos": "all",
            "variaveis": "11602",  # Variacao m/m-12
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "544[129314]",
        },
        "description": "Producao Industrial Mensal - Variacao m/m-12",
    },
    "pim_ytd": {
        "code": 8888,
        "name": "PIM - Variacao YTD",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8888",
            "periodos": "all",
            "variaveis": "11603",  # Variacao acumulada no ano
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "544[129314]",
        },
        "description": "Producao Industrial Mensal - Variacao acumulada no ano",
    },
    "pim_12m": {
        "code": 8888,
        "name": "PIM - Variacao 12 meses",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8888",
            "periodos": "all",
            "variaveis": "11604",  # Variacao acumulada 12 meses
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "544[129314]",
        },
        "description": "Producao Industrial Mensal - Variacao acumulada 12 meses",
    },
    "pmc_varejo": {
        "code": 8880,
        "name": "PMC - Varejo",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8880",
            "periodos": "all",
            "variaveis": "7169",  # Volume de Vendas
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56734]",  # Indice de volume
        },
        "description": "Pesquisa Mensal de Comercio - Varejo (Volume)",
    },
    "pmc_varejo_dessaz": {
        "code": 8880,
        "name": "PMC - Varejo (Dessaz)",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8880",
            "periodos": "all",
            "variaveis": "7170",  # Numero-indice com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56734]",
        },
        "description": "Pesquisa Mensal de Comercio - Varejo Dessazonalizado",
    },
    "pmc_varejo_mom": {
        "code": 8880,
        "name": "PMC - Varejo MoM",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8880",
            "periodos": "all",
            "variaveis": "11708",  # Variacao m/m-1 com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56734]",
        },
        "description": "Pesquisa Mensal de Comercio - Varejo MoM (dessaz)",
    },
    "pmc_varejo_yoy": {
        "code": 8880,
        "name": "PMC - Varejo YoY",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8880",
            "periodos": "all",
            "variaveis": "11709",  # Variacao m/m-12
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56734]",
        },
        "description": "Pesquisa Mensal de Comercio - Varejo YoY",
    },
    "pmc_varejo_ytd": {
        "code": 8880,
        "name": "PMC - Varejo YTD",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8880",
            "periodos": "all",
            "variaveis": "11710",  # Variacao acumulada no ano
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56734]",
        },
        "description": "Pesquisa Mensal de Comercio - Varejo YTD",
    },
    "pmc_varejo_12m": {
        "code": 8880,
        "name": "PMC - Varejo 12m",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8880",
            "periodos": "all",
            "variaveis": "11711",  # Variacao acumulada 12 meses
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56734]",
        },
        "description": "Pesquisa Mensal de Comercio - Varejo 12 meses",
    },
    "pmc_ampliado": {
        "code": 8881,
        "name": "PMC - Varejo Ampliado",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8881",
            "periodos": "all",
            "variaveis": "7169",  # Volume de Vendas
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56736]",  # Indice de volume ampliado
        },
        "description": "Pesquisa Mensal de Comercio - Varejo Ampliado (Volume)",
    },
    "pmc_ampliado_dessaz": {
        "code": 8881,
        "name": "PMC - Ampliado (Dessaz)",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8881",
            "periodos": "all",
            "variaveis": "7170",  # Numero-indice com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56736]",
        },
        "description": "Pesquisa Mensal de Comercio - Ampliado Dessazonalizado",
    },
    "pmc_ampliado_mom": {
        "code": 8881,
        "name": "PMC - Ampliado MoM",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8881",
            "periodos": "all",
            "variaveis": "11708",  # Variacao m/m-1 com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56736]",
        },
        "description": "Pesquisa Mensal de Comercio - Ampliado MoM (dessaz)",
    },
    "pmc_ampliado_yoy": {
        "code": 8881,
        "name": "PMC - Ampliado YoY",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8881",
            "periodos": "all",
            "variaveis": "11709",  # Variacao m/m-12
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56736]",
        },
        "description": "Pesquisa Mensal de Comercio - Ampliado YoY",
    },
    "pmc_ampliado_ytd": {
        "code": 8881,
        "name": "PMC - Ampliado YTD",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8881",
            "periodos": "all",
            "variaveis": "11710",  # Variacao acumulada no ano
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56736]",
        },
        "description": "Pesquisa Mensal de Comercio - Ampliado YTD",
    },
    "pmc_ampliado_12m": {
        "code": 8881,
        "name": "PMC - Ampliado 12m",
        "frequency": "monthly",
        "parameters": {
            "agregados": "8881",
            "periodos": "all",
            "variaveis": "11711",  # Variacao acumulada 12 meses
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56736]",
        },
        "description": "Pesquisa Mensal de Comercio - Ampliado 12 meses",
    },
    "pms": {
        "code": 5906,
        "name": "PMS - Servicos",
        "frequency": "monthly",
        "parameters": {
            "agregados": "5906",
            "periodos": "all",
            "variaveis": "7167",  # Volume de Servicos
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56726]",  # Indice de volume
        },
        "description": "Pesquisa Mensal de Servicos - Volume",
    },
    "pms_dessaz": {
        "code": 5906,
        "name": "PMS - Servicos (Dessaz)",
        "frequency": "monthly",
        "parameters": {
            "agregados": "5906",
            "periodos": "all",
            "variaveis": "7168",  # Numero-indice com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56726]",
        },
        "description": "Pesquisa Mensal de Servicos - Dessazonalizado",
    },
    "pms_mom": {
        "code": 5906,
        "name": "PMS - Servicos MoM",
        "frequency": "monthly",
        "parameters": {
            "agregados": "5906",
            "periodos": "all",
            "variaveis": "11623",  # Variacao m/m-1 com ajuste sazonal
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56726]",
        },
        "description": "Pesquisa Mensal de Servicos - MoM (dessaz)",
    },
    "pms_yoy": {
        "code": 5906,
        "name": "PMS - Servicos YoY",
        "frequency": "monthly",
        "parameters": {
            "agregados": "5906",
            "periodos": "all",
            "variaveis": "11624",  # Variacao m/m-12
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56726]",
        },
        "description": "Pesquisa Mensal de Servicos - YoY",
    },
    "pms_ytd": {
        "code": 5906,
        "name": "PMS - Servicos YTD",
        "frequency": "monthly",
        "parameters": {
            "agregados": "5906",
            "periodos": "all",
            "variaveis": "11625",  # Variacao acumulada no ano
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56726]",
        },
        "description": "Pesquisa Mensal de Servicos - YTD",
    },
    "pms_12m": {
        "code": 5906,
        "name": "PMS - Servicos 12m",
        "frequency": "monthly",
        "parameters": {
            "agregados": "5906",
            "periodos": "all",
            "variaveis": "11626",  # Variacao acumulada 12 meses
            "nivel_territorial": "1",
            "localidades": "all",
            "classification": "11046[56726]",
        },
        "description": "Pesquisa Mensal de Servicos - 12 meses",
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
        "code": 6381,
        "name": "Taxa de Desocupacao (PNAD)",
        "frequency": "monthly",  # Trimestres moveis com publicacao mensal
        "parameters": {
            "agregados": "6381",
            "periodos": "all",
            "variaveis": "4099",  # Taxa de desocupacao
            "nivel_territorial": "1",
            "localidades": "all",
        },
        "description": "Taxa de Desocupacao - PNAD Continua (Trimestre Movel)",
    }
}
