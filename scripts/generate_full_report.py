"""
Geracao de graficos economicos.

Gera visualizacoes padronizadas para relatorios de research.

Uso:
    uv run python scripts/generate_full_report.py
"""

from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from dateutil.relativedelta import relativedelta

# Agora-Database
from adb import sgs, sidra, bloomberg, ipea
from adb.providers.bloomberg.indicators import GLOBAL_DY, GLOBAL_PE_FWD

# Chartkit (biblioteca de graficos)
import chartkit

# Periodo padrao para filtros (em anos)
ANOS_PADRAO = 12
ANOS_BBG = 5
ANOS_JUROS_REAL = 26


def get_start_date(years: int) -> str:
    """
    Calcula data de inicio para filtro de N anos atras.

    Args:
        years: Numero de anos para voltar no tempo.

    Returns:
        Data no formato 'YYYY-MM-DD'.
    """
    cutoff = datetime.now() - relativedelta(years=years)
    return cutoff.strftime("%Y-%m-%d")


# Datas de corte pre-calculadas
START_PADRAO = get_start_date(ANOS_PADRAO)
START_BBG = get_start_date(ANOS_BBG)
START_JUROS_REAL = get_start_date(ANOS_JUROS_REAL)


def save_chart(
    df, filename, title, source=None, kind="line", units="%", highlight=True, **kwargs
):
    """
    Helper para gerar e salvar grafico.

    Args:
        df: DataFrame com dados a plotar.
        filename: Nome do arquivo de saida.
        title: Titulo do grafico.
        source: Fonte dos dados (opcional).
        kind: Tipo de grafico ('line' ou 'bar').
        units: Unidade dos dados para formatacao do eixo Y.
        highlight: Modo de highlight (True, "all", ["max", "min"], etc).
        **kwargs: Argumentos adicionais para o plot.
    """
    if df.empty:
        print(f"  [SKIP] {title} - dados vazios")
        return

    result = df.chartkit.plot(
        kind=kind,
        title=title,
        units=units,
        source=source,
        highlight=highlight,
        **kwargs,
    )
    result.save(filename)
    print(f"  [OK] {filename}")
    plt.close("all")


# =============================================================================
# 1. ATIVIDADE ECONOMICA - IBC-BR
# =============================================================================
print("\n[1] Atividade Economica - IBC-BR")

# IBC-BR Agregado
save_chart(
    sgs.read("ibc_br_dessaz", start=START_PADRAO),
    filename="ibc_br_agregado.png",
    title="IBC-BR (Dessazonalizado)",
    source="BCB",
    kind="line",
    units="points",
)

# IBC-BR Setorial
df_ibc_setorial = pd.concat(
    [
        sgs.read("ibc_br_agro", start=START_PADRAO),
        sgs.read("ibc_br_industria", start=START_PADRAO),
        sgs.read("ibc_br_servicos", start=START_PADRAO),
    ],
    axis=1,
)
df_ibc_setorial.columns = ["Agropecuária", "Indústria", "Serviços"]
save_chart(
    df_ibc_setorial,
    filename="ibc_br_setorial.png",
    title="IBC-BR por Setor",
    source="BCB",
    kind="line",
    units="points",
)


# =============================================================================
# 2. PIB
# =============================================================================
print("\n[2] PIB")

# PIB QoQ
save_chart(
    sidra.read("pib_qoq", start=START_PADRAO),
    filename="pib_qoq.png",
    title="PIB (Variação Trimestral)",
    source="IBGE",
    kind="bar",
    units="%",
    y_origin="auto",
    tick_freq="year"
)

# PIB YoY
save_chart(
    sidra.read("pib_yoy", start=START_PADRAO),
    filename="pib_yoy.png",
    title="PIB (Variação Anual)",
    source="IBGE",
    kind="bar",
    units="%",
    y_origin="auto",
    tick_rotation=90,
    tick_freq="year"
)


# =============================================================================
# 3. PRODUCAO INDUSTRIAL (PIM)
# =============================================================================
print("\n[3] Producao Industrial")

# PIM
save_chart(
    sidra.read("pim_dessaz", start=START_PADRAO),
    filename="pim_indice.png",
    title="Produção Industrial",
    source="IBGE",
    kind="line",
    units="points",
)


# =============================================================================
# 4. COMERCIO (PMC)
# =============================================================================
print("\n[4] Comercio")

# PMC Varejo
save_chart(
    sidra.read("pmc_varejo_dessaz", start=START_PADRAO),
    filename="pmc_varejo_indice.png",
    title="Varejo - Volume de Vendas",
    source="IBGE",
    kind="line",
    units="points",
)

# PMC Ampliado
save_chart(
    sidra.read("pmc_ampliado_dessaz", start=START_PADRAO),
    filename="pmc_ampliado_indice.png",
    title="Varejo Ampliado - Volume de Vendas",
    source="IBGE",
    kind="line",
    units="points",
)


# =============================================================================
# 5. SERVICOS (PMS)
# =============================================================================
print("\n[5] Servicos")

# PMS
save_chart(
    sidra.read("pms_dessaz", start=START_PADRAO),
    filename="pms_indice.png",
    title="Serviços - Volume",
    source="IBGE",
    kind="line",
    units="points",
)

# PMS YoY
save_chart(
    sidra.read("pms_yoy", start=START_PADRAO),
    filename="pms_yoy.png",
    title="Serviços - Volume (Variação Anual)",
    source="IBGE",
    kind="bar",
    units="%",
    y_origin="auto",
)


# =============================================================================
# 6. MERCADO DE TRABALHO
# =============================================================================
print("\n[6] Mercado de Trabalho")

# PNAD Taxa de Desemprego
save_chart(
    sidra.read("pnad_desocupacao", start=START_PADRAO),
    filename="pnad_desemprego.png",
    title="Taxa de Desemprego (PNAD)",
    source="IBGE",
    kind="line",
    units="%",
)

# CAGED saldo
save_chart(
    ipea.read("caged_saldo", start=START_PADRAO),
    filename="caged_saldo.png",
    title="Saldo Caged",
    source="IPEA",
    kind="bar",
    units="points",
)

# =============================================================================
# 7. INFLACAO
# =============================================================================
print("\n[7] Inflacao")

# IPCA Mensal
save_chart(
    sidra.read("ipca", start=START_PADRAO),
    filename="ipca_mensal.png",
    title="IPCA (Variação Mensal)",
    source="IBGE",
    kind="bar",
    units="%",
    y_origin="auto",
)

# IPCA 12m
save_chart(
    sidra.read("ipca_12m", start=START_PADRAO),
    filename="ipca_12m.png",
    title="IPCA (Acumulado 12 meses)",
    source="IBGE",
    kind="line",
    units="%",
)


# =============================================================================
# 8. JUROS E CAMBIO
# =============================================================================
print("\n[8] Juros e Cambio")

# Cambio
df_dolar = sgs.read("dolar_ptax", start=START_PADRAO)
df_euro = sgs.read("euro_ptax", start=START_PADRAO)
df_cambio = pd.concat([df_dolar, df_euro], axis=1)
df_cambio.columns = ["Dólar", "Euro"]
save_chart(
    df_cambio,
    filename="cambio.png",
    title="Taxa de Câmbio (PTAX)",
    source="BCB",
    kind="line",
    units="BRL",
)

# Selic
save_chart(
    sgs.read("selic", start=START_PADRAO),
    filename="selic.png",
    title="Taxa Selic (Meta)",
    source="BCB",
    kind="line",
    units="%",
)

# Juros real (precisa de dados desde o inicio do periodo de 26 anos para calculo rolling)
ipca = chartkit.to_month_end(sidra.read("ipca_12m", start=START_JUROS_REAL))
selic = chartkit.to_month_end(sgs.read("selic_acum_mensal", start=START_JUROS_REAL))

# Selic 12m composta e juros real via Fisher
selic_12m = chartkit.accum(selic["selic_acum_mensal"])
juros_real = ((1 + selic_12m / 100) / (1 + ipca["ipca_12m"] / 100) - 1) * 100
juros_real = juros_real.dropna().to_frame("juros_real")

save_chart(
    juros_real,
    filename="juros_reais.png",
    title="Juros Reais ex-post",
    source="BCB, IBGE",
    kind="line",
    units="%",
)

# =============================================================================
# 9. BLOOMBERG
# =============================================================================
print("\n[9] Bloomberg")

# Global Mkt Cap
save_chart(
    bloomberg.read("msci_acwi_mktcap", start=START_BBG),
    filename="global_mktcap.png",
    title="Market Cap Global",
    source="Bloomberg",
    kind="line",
    units="USD",
)

# Global P/L
save_chart(
    bloomberg.read("msci_acwi_pe", start=START_BBG),
    filename="global_pl.png",
    title="P/L Global",
    source="Bloomberg",
    kind="line",
    units="USD",
)

# Global Dividends
save_chart(
    bloomberg.read("msci_acwi_dividend", start=START_BBG),
    filename="global_dividends.png",
    title="Dividendos Global",
    source="Bloomberg",
    kind="line",
    units="%",
)

# Ibovespa
save_chart(
    bloomberg.read("ibov_points", start=START_BBG),
    filename="ibovespa.png",
    title="Ibovespa",
    source="Bloomberg",
    kind="line",
    units="points",
)

# Ibovespa em Dolar
save_chart(
    bloomberg.read("ibov_usd", start=START_BBG),
    filename="ibovespa_usd.png",
    title="Ibovespa (Dólar)",
    source="Bloomberg",
    kind="line",
    units="points",
)

# P/E Fwd Ibovespa
save_chart(
    bloomberg.read("ibov_pe_fwd", start=START_BBG),
    filename="ibovespa_pe_fwd.png",
    title="P/E Fwd Ibovespa",
    source="Bloomberg",
    kind="line",
    units="x",
)

# DY Ibovespa
save_chart(
    bloomberg.read("ibov_dy", start=START_BBG),
    filename="ibovespa_dy.png",
    title="DY Ibovespa",
    source="Bloomberg",
    kind="line",
    units="%",
)

# IFIX
save_chart(
    bloomberg.read("ifix", start=START_BBG),
    filename="ifix.png",
    title="IFIX",
    source="Bloomberg",
    kind="line",
    units="points",
)

# Petroleo Brent
save_chart(
    bloomberg.read("brent", start=START_BBG),
    filename="brent.png",
    title="Petróleo (Brent)",
    source="Bloomberg",
    kind="line",
    units="USD",
)

# Minerio de Ferro
save_chart(
    bloomberg.read("iron_ore", start=START_BBG),
    filename="iron.png",
    title="Minério de Ferro",
    source="Bloomberg",
    kind="line",
    units="USD",
)

# Ouro
save_chart(
    bloomberg.read("gold", start=START_BBG),
    filename="gold.png",
    title="Ouro",
    source="Bloomberg",
    kind="line",
    units="USD",
)

# IGPM
save_chart(
    bloomberg.read("igpm", start=START_BBG),
    filename="igpm.png",
    title="IGPM",
    source="Bloomberg",
    kind="line",
    units="%",
)

# =============================================================================
# 10. VALUATIONS GLOBAIS
# =============================================================================
print("\n[10] Valuations Globais")

PE_FWD_LABELS: dict[str, str] = {
    "cac_pe_fwd": "CAC 40",
    "dax_pe_fwd": "DAX",
    "dm_pe_fwd": "MSCI DM",
    "ftsemib_pe_fwd": "FTSE MIB",
    "ibov_pe_fwd": "Ibovespa",
    "merval_pe_fwd": "MERVAL",
    "mexbol_pe_fwd": "IPC Mexico",
    "mxef_pe_fwd": "MSCI EM",
    "mxwo_pe_fwd": "MSCI World",
    "nky_pe_fwd": "Nikkei 225",
    "sensex_pe_fwd": "Sensex",
    "shcomp_pe_fwd": "Shanghai",
    "spx_pe_fwd": "S&P 500",
}

DY_LABELS: dict[str, str] = {
    "cac_dy": "CAC 40",
    "dax_dy": "DAX",
    "dm_dy": "MSCI DM",
    "ibov_dy": "Ibovespa",
    "ipsa_dy": "IPSA Chile",
    "jalsh_dy": "JSE All Share",
    "merval_dy": "MERVAL",
    "mexbol_dy": "IPC Mexico",
    "mxef_dy": "MSCI EM",
    "nky_dy": "Nikkei 225",
    "sensex_dy": "Sensex",
    "shcomp_dy": "Shanghai",
    "spx_dy": "S&P 500",
    "ukx_dy": "FTSE 100",
}

# P/E Forward - Bolsas Globais
df_pe_global = bloomberg.read(*GLOBAL_PE_FWD)
if not df_pe_global.empty:
    last_pe = (
        df_pe_global.ffill()
        .iloc[-1]
        .rename(PE_FWD_LABELS)
        .dropna()
        .to_frame("P/E Forward")
    )
    save_chart(
        last_pe,
        filename="global_pe_fwd.png",
        title="P/E Forward - Bolsas Globais",
        source="Bloomberg",
        kind="bar",
        units="x",
        highlight="all",
        sort="descending",
        color="cycle",
    )

# Dividend Yield - Bolsas Globais
df_dy_global = bloomberg.read(*GLOBAL_DY)
if not df_dy_global.empty:
    last_dy = (
        df_dy_global.ffill()
        .iloc[-1]
        .rename(DY_LABELS)
        .dropna()
        .to_frame("Dividend Yield")
    )
    save_chart(
        last_dy,
        filename="global_dy.png",
        title="Dividend Yield - Bolsas Globais",
        source="Bloomberg",
        kind="bar",
        units="%",
        highlight="all",
        sort="descending",
        color="cycle",
    )


# =============================================================================
# RESUMO
# =============================================================================
print(f"\n{'=' * 50}")
print(f"Graficos gerados em: {chartkit.CHARTS_PATH}")
print(f"Total: {len(list(chartkit.CHARTS_PATH.glob('*.png')))} arquivos")
