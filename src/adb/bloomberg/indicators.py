"""
Configuracao de indicadores Bloomberg disponiveis.

Series temporais de mercado via Bloomberg Terminal (xbbg).
"""

# =============================================================================
# CONSTANTES
# =============================================================================

# Lookback maximo para primeira execucao (evitar quotas Bloomberg)
LOOKBACK_DAYS = 730  # 2 anos de historico

# =============================================================================
# CONFIGURACAO DE INDICADORES BLOOMBERG
# =============================================================================

BLOOMBERG_CONFIG = {
    # === GLOBAL EQUITIES ===
    "msci_acwi_mktcap": {
        "ticker": "MXWD Index",
        "fields": ["CUR_MKT_CAP"],
        "name": "MSCI ACWI - Market Cap",
        "frequency": "daily",
        "description": "Capitalizacao de mercado MSCI All Country World Index",
        "category": "global_equities",
    },
    "msci_acwi_pe": {
        "ticker": "MXWD Index",
        "fields": ["BEST_PE_RATIO"],
        "name": "MSCI ACWI - P/E Ratio",
        "frequency": "daily",
        "description": "Price-to-Earnings ratio MSCI All Country World Index",
        "category": "global_equities",
    },
    "msci_acwi_dividend": {
        "ticker": "MXWD Index",
        "fields": ["EQY_DVD_YLD_12M"],
        "name": "MSCI ACWI - Dividend Yield",
        "frequency": "daily",
        "description": "Dividend Yield 12M MSCI All Country World Index",
        "category": "global_equities",
    },
    # === BRASIL EQUITIES ===
    "ibov_points": {
        "ticker": "IBOV Index",
        "fields": ["PX_LAST"],
        "name": "Ibovespa - Pontos",
        "frequency": "daily",
        "description": "Indice Ibovespa em pontos",
        "category": "brazil_equities",
    },
    "ibov_usd": {
        "ticker": "USIBOV Index",
        "fields": ["PX_LAST"],
        "name": "Ibovespa - USD",
        "frequency": "daily",
        "description": "Indice Ibovespa em dolares",
        "category": "brazil_equities",
    },
    "ifix": {
        "ticker": "IFIX Index",
        "fields": ["PX_LAST"],
        "name": "IFIX",
        "frequency": "daily",
        "description": "Indice de Fundos de Investimentos Imobiliarios",
        "category": "brazil_equities",
    },
    # === COMMODITIES ===
    "brent": {
        "ticker": "CO1 Comdty",
        "fields": ["PX_LAST"],
        "name": "Brent Crude",
        "frequency": "daily",
        "description": "Petroleo Brent - Contrato Futuro Generico 1",
        "category": "commodities",
    },
    "iron_ore": {
        "ticker": "SCOA Comdty",
        "fields": ["PX_LAST"],
        "name": "Iron Ore",
        "frequency": "daily",
        "description": "Minerio de Ferro SGX 62% Fe",
        "category": "commodities",
    },
    "gold": {
        "ticker": "XAU Curncy",
        "fields": ["PX_LAST"],
        "name": "Gold Spot",
        "frequency": "daily",
        "description": "Ouro Spot em USD",
        "category": "commodities",
    },
}
