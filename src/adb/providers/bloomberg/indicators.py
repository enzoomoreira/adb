"""
Configuracao de indicadores Bloomberg disponiveis.

Series temporais de mercado via Bloomberg Terminal (xbbg).
"""

# =============================================================================
# CONSTANTES
# =============================================================================

# Lookback maximo para primeira execucao (evitar quotas Bloomberg)
LOOKBACK_DAYS = 365 * 6

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
    "ibov_dy": {
        "ticker": "IBOV Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "Ibovespa - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso Ibovespa",
        "category": "equity_valuations",
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
    # === INDICES DE INFLACAO ===
    "igpm": {
        "ticker": "IBREGPMY Index",
        "fields": ["PX_LAST"],
        "name": "IGPM-10",
        "frequency": "monthly",
        "description": "Indice IGPM-10 FGV",
        "category": "indexes",
    },
    # === EQUITY VALUATIONS ===
    "cac_dy": {
        "ticker": "CAC Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "CAC 40 - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso CAC 40",
        "category": "equity_valuations",
    },
    "cac_pe_fwd": {
        "ticker": "CAC Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "CAC 40 - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso CAC 40",
        "category": "equity_valuations",
    },
    "dax_dy": {
        "ticker": "DAX Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "DAX - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso DAX",
        "category": "equity_valuations",
    },
    "dax_pe_fwd": {
        "ticker": "DAX Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "DAX - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso DAX",
        "category": "equity_valuations",
    },
    "dm_dy": {
        "ticker": "DM Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "MSCI DM - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso MSCI Developed Markets",
        "category": "equity_valuations",
    },
    "dm_pe_fwd": {
        "ticker": "DM Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "MSCI DM - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso MSCI Developed Markets",
        "category": "equity_valuations",
    },
    "ftsemib_pe_fwd": {
        "ticker": "FTSEMIB Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "FTSE MIB - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso FTSE MIB",
        "category": "equity_valuations",
    },
    "ibov_pe_fwd": {
        "ticker": "IBOV Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "Ibovespa - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso Ibovespa",
        "category": "equity_valuations",
    },
    "ipsa_dy": {
        "ticker": "IPSA Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "IPSA Chile - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso IPSA Chile",
        "category": "equity_valuations",
    },
    "jalsh_dy": {
        "ticker": "JALSH Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "JSE All Share - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso JSE All Share",
        "category": "equity_valuations",
    },
    "merval_dy": {
        "ticker": "MERVAL Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "MERVAL - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso MERVAL",
        "category": "equity_valuations",
    },
    "merval_pe_fwd": {
        "ticker": "MERVAL Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "MERVAL - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso MERVAL",
        "category": "equity_valuations",
    },
    "mexbol_dy": {
        "ticker": "MEXBOL Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "IPC Mexico - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso IPC Mexico",
        "category": "equity_valuations",
    },
    "mexbol_pe_fwd": {
        "ticker": "MEXBOL Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "IPC Mexico - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso IPC Mexico",
        "category": "equity_valuations",
    },
    "mxef_dy": {
        "ticker": "MXEF Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "MSCI EM - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso MSCI Emerging Markets",
        "category": "equity_valuations",
    },
    "mxef_pe_fwd": {
        "ticker": "MXEF Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "MSCI EM - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso MSCI Emerging Markets",
        "category": "equity_valuations",
    },
    "mxwo_pe_fwd": {
        "ticker": "MXWO Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "MSCI World - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso MSCI World",
        "category": "equity_valuations",
    },
    "nky_dy": {
        "ticker": "NKY Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "Nikkei 225 - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso Nikkei 225",
        "category": "equity_valuations",
    },
    "nky_pe_fwd": {
        "ticker": "NKY Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "Nikkei 225 - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso Nikkei 225",
        "category": "equity_valuations",
    },
    "sensex_dy": {
        "ticker": "SENSEX Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "Sensex - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso Sensex",
        "category": "equity_valuations",
    },
    "sensex_pe_fwd": {
        "ticker": "SENSEX Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "Sensex - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso Sensex",
        "category": "equity_valuations",
    },
    "shcomp_dy": {
        "ticker": "SHCOMP Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "Shanghai Comp - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso Shanghai Composite",
        "category": "equity_valuations",
    },
    "shcomp_pe_fwd": {
        "ticker": "SHCOMP Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "Shanghai Comp - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso Shanghai Composite",
        "category": "equity_valuations",
    },
    "spx_dy": {
        "ticker": "SPX Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "S&P 500 - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso S&P 500",
        "category": "equity_valuations",
    },
    "spx_pe_fwd": {
        "ticker": "SPX Index",
        "fields": ["GEN_EST_PE_NEXT_YR_AGGTE"],
        "name": "S&P 500 - P/E Fwd",
        "frequency": "daily",
        "description": "P/E Forward consenso S&P 500",
        "category": "equity_valuations",
    },
    "ukx_dy": {
        "ticker": "UKX Index",
        "fields": ["BEST_DIV_YLD"],
        "name": "FTSE 100 - DY",
        "frequency": "daily",
        "description": "Dividend Yield consenso FTSE 100",
        "category": "equity_valuations",
    },
}

# =============================================================================
# CONSTANTES DE GRUPO
# =============================================================================

GLOBAL_PE_FWD: list[str] = [
    "cac_pe_fwd",
    "dax_pe_fwd",
    "dm_pe_fwd",
    "ftsemib_pe_fwd",
    "ibov_pe_fwd",
    "merval_pe_fwd",
    "mexbol_pe_fwd",
    "mxef_pe_fwd",
    "mxwo_pe_fwd",
    "nky_pe_fwd",
    "sensex_pe_fwd",
    "shcomp_pe_fwd",
    "spx_pe_fwd",
]

GLOBAL_DY: list[str] = [
    "cac_dy",
    "dax_dy",
    "dm_dy",
    "ibov_dy",
    "ipsa_dy",
    "jalsh_dy",
    "merval_dy",
    "mexbol_dy",
    "mxef_dy",
    "nky_dy",
    "sensex_dy",
    "shcomp_dy",
    "spx_dy",
    "ukx_dy",
]
