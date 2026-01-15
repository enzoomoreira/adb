"""
Configuracao de indicadores e endpoints para expectativas do BCB (Relatorio Focus).

Estrutura similar ao modulo SGS para consistencia.
"""

# =============================================================================
# ENDPOINTS da API de Expectativas
# =============================================================================

ENDPOINTS = {
    # Anuais
    "top5_anuais": "ExpectativasMercadoTop5Anuais",
    "anuais": "ExpectativasMercadoAnuais",
    # Mensais
    "mensais": "ExpectativaMercadoMensais",
    "top5_mensais": "ExpectativasMercadoTop5Mensais",
    # Trimestrais
    "trimestrais": "ExpectativasMercadoTrimestrais",
    "top5_trimestrais": "ExpectativaMercadoTop5Trimestral",
    # Selic
    "selic": "ExpectativasMercadoSelic",
    "top5_selic": "ExpectativasMercadoTop5Selic",
    # Inflacao suavizada
    "inflacao_12m": "ExpectativasMercadoInflacao12Meses",
    "inflacao_24m": "ExpectativasMercadoInflacao24Meses",
    "top5_inflacao_12m": "ExpectativasMercadoTop5Inflacao12Meses",
    "top5_inflacao_24m": "ExpectativasMercadoTop5Inflacao24Meses",
}

# =============================================================================
# INDICADORES disponiveis por tipo de endpoint
# =============================================================================

# Top5 Anuais e Anuais
ANNUAL_INDICATORS = [
    "IPCA",
    "IGP-M",
    "PIB Total",
    "Câmbio",
    "Selic",
    "IGP-DI",
    "INPC",
    "IPA-M",
    "Produção industrial",
    "Balança comercial",
    "Conta corrente",
    "Investimento direto no país",
    "Dívida líquida do setor público",
    "Resultado primário",
    "Resultado nominal",
]

# Indicadores de inflacao (endpoints 12m e 24m)
INFLATION_INDICATORS = [
    "IPCA",
    "IGP-M",
    "IGP-DI",
    "INPC",
]

# Indicadores mensais
MONTHLY_INDICATORS = [
    "IPCA",
    "IGP-M",
    "Câmbio",
    "IPCA Administrados",
    "IPCA Alimentação no domicílio",
    "IPCA Bens industrializados",
    "IPCA Livres",
    "IPCA Serviços",
    "Taxa de desocupação",
]

# Mapeamento de nomes amigaveis
INDICATOR_NAMES = {
    "ipca": "IPCA",
    "igpm": "IGP-M",
    "igpdi": "IGP-DI",
    "inpc": "INPC",
    "pib": "PIB Total",
    "cambio": "Câmbio",
    "selic": "Selic",
    "producao_industrial": "Produção industrial",
    "balanca_comercial": "Balança comercial",
}

# =============================================================================
# CONFIGURACAO para coleta automatica
# =============================================================================

EXPECTATIONS_CONFIG = {
    # === ANUAIS (Top 5 previsores) ===
    "ipca_anual": {
        "endpoint": "top5_anuais",
        "indicator": "IPCA",
        "description": "Expectativa IPCA anual (Top 5 previsores)",
    },
    "igpm_anual": {
        "endpoint": "top5_anuais",
        "indicator": "IGP-M",
        "description": "Expectativa IGP-M anual (Top 5 previsores)",
    },
    "pib_anual": {
        "endpoint": "top5_anuais",
        "indicator": "PIB Total",
        "description": "Expectativa PIB anual (Top 5 previsores)",
    },
    "cambio_anual": {
        "endpoint": "top5_anuais",
        "indicator": "Câmbio",
        "description": "Expectativa Câmbio fim de ano (Top 5 previsores)",
    },
    "selic_anual": {
        "endpoint": "top5_anuais",
        "indicator": "Selic",
        "description": "Expectativa Selic fim de ano (Top 5 previsores)",
    },
    # === MENSAIS ===
    "ipca_mensal": {
        "endpoint": "mensais",
        "indicator": "IPCA",
        "description": "Expectativa IPCA mensal",
    },
    "igpm_mensal": {
        "endpoint": "mensais",
        "indicator": "IGP-M",
        "description": "Expectativa IGP-M mensal",
    },
    "cambio_mensal": {
        "endpoint": "mensais",
        "indicator": "Câmbio",
        "description": "Expectativa Câmbio mensal",
    },
    # === SELIC (por reuniao COPOM) ===
    "selic": {
        "endpoint": "selic",
        "indicator": "Selic",
        "description": "Expectativa Selic por reuniao COPOM",
    },
    # === INFLACAO SUAVIZADA ===
    "ipca_12m": {
        "endpoint": "inflacao_12m",
        "indicator": "IPCA",
        "description": "Expectativa IPCA acumulado 12 meses",
    },
    "ipca_24m": {
        "endpoint": "inflacao_24m",
        "indicator": "IPCA",
        "description": "Expectativa IPCA acumulado 24 meses",
    },
    "igpm_12m": {
        "endpoint": "inflacao_12m",
        "indicator": "IGP-M",
        "description": "Expectativa IGP-M acumulado 12 meses",
    },
}
