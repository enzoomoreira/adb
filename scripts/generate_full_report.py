"""
Geracao de graficos economicos.

Gera visualizacoes padronizadas para relatorios de research.

Uso:
    uv run python scripts/generate_full_report.py
"""

import pandas as pd
import matplotlib.pyplot as plt

# Agora-Database
from adb import sgs, sidra, charting

# Periodo padrao para filtros
ANOS_PADRAO = 12


def save_chart(df, filename, title, source=None, kind='line', units='%', years=None, **kwargs):
    """Helper para gerar e salvar grafico."""
    # Filtra por periodo se especificado
    if years and isinstance(df.index, pd.DatetimeIndex):
        cutoff = pd.Timestamp.now() - pd.DateOffset(years=years)
        df = df[df.index >= cutoff]

    if df.empty:
        print(f"  [SKIP] {title} - dados vazios")
        return

    # Gera grafico
    df.agora.plot(
        kind=kind,
        title=title,
        units=units,
        source=source,
        highlight_last=(kind == 'line'),
        save_path=filename,
        **kwargs
    )
    print(f"  [OK] {filename}")
    plt.close('all')


# =============================================================================
# 1. ATIVIDADE ECONOMICA - IBC-BR
# =============================================================================
print("\n[1] Atividade Economica - IBC-BR")

# IBC-BR Agregado (linha)
save_chart(
    sgs.read('ibc_br_dessaz'),
    filename="ibc_br_agregado.png",
    title="IBC-BR (Dessazonalizado)",
    source="BCB",
    kind='line',
    units='points',
    years=ANOS_PADRAO
)

# IBC-BR Setorial (linhas sobrepostas)
try:
    df_agro = sgs.read('ibc_br_agro')
    df_ind = sgs.read('ibc_br_industria')
    df_serv = sgs.read('ibc_br_servicos')
    df_ibc_setores = pd.concat([df_agro, df_ind, df_serv], axis=1)
    df_ibc_setores.columns = ['Agropecuária', 'Indústria', 'Serviços']
    save_chart(
        df_ibc_setores,
        filename="ibc_br_setorial.png",
        title="IBC-BR por Setor",
        source="BCB",
        kind='line',
        units='points',
        years=ANOS_PADRAO
    )
except Exception as e:
    print(f"  [SKIP] IBC-BR Setorial - {e}")


# =============================================================================
# 2. PIB
# =============================================================================
print("\n[2] PIB")

# PIB QoQ (barras)
save_chart(
    sidra.read('pib_qoq'),
    filename="pib_qoq.png",
    title="PIB (Variação Trimestral)",
    source="IBGE",
    kind='bar',
    units='%',
    years=ANOS_PADRAO,
    y_origin='auto'
)

# PIB YoY (barras)
save_chart(
    sidra.read('pib_yoy'),
    filename="pib_yoy.png",
    title="PIB (Variação Anual)",
    source="IBGE",
    kind='bar',
    units='%',
    years=ANOS_PADRAO,
    y_origin='auto'
)


# =============================================================================
# 3. PRODUCAO INDUSTRIAL (PIM)
# =============================================================================
print("\n[3] Producao Industrial")

# PIM Base 100 (linha)
save_chart(
    sidra.read('pim_dessaz'),
    filename="pim_indice.png",
    title="Produção Industrial (Índice Base 100)",
    source="IBGE",
    kind='line',
    units='points',
    years=ANOS_PADRAO
)


# =============================================================================
# 4. COMERCIO (PMC)
# =============================================================================
print("\n[4] Comercio")

# PMC Varejo Base 100 (linha)
save_chart(
    sidra.read('pmc_varejo_dessaz'),
    filename="pmc_varejo_indice.png",
    title="Varejo - Volume de Vendas (Índice Base 100)",
    source="IBGE",
    kind='line',
    units='points',
    years=ANOS_PADRAO
)

# PMC Ampliado Base 100 (linha)
save_chart(
    sidra.read('pmc_ampliado_dessaz'),
    filename="pmc_ampliado_indice.png",
    title="Varejo Ampliado - Volume de Vendas (Índice Base 100)",
    source="IBGE",
    kind='line',
    units='points',
    years=ANOS_PADRAO
)


# =============================================================================
# 5. SERVICOS (PMS)
# =============================================================================
print("\n[5] Servicos")

# PMS Base 100 (linha)
save_chart(
    sidra.read('pms_dessaz'),
    filename="pms_indice.png",
    title="Serviços (Índice Base 100)",
    source="IBGE",
    kind='line',
    units='points',
    years=ANOS_PADRAO
)

# PMS YoY (barras)
save_chart(
    sidra.read('pms_yoy'),
    filename="pms_yoy.png",
    title="Serviços (Variação Anual)",
    source="IBGE",
    kind='bar',
    units='%',
    years=ANOS_PADRAO,
    y_origin='auto'
)


# =============================================================================
# 6. MERCADO DE TRABALHO
# =============================================================================
print("\n[6] Mercado de Trabalho")

# PNAD Taxa de Desemprego (linha)
save_chart(
    sidra.read('pnad_desocupacao'),
    filename="pnad_desemprego.png",
    title="Taxa de Desemprego (PNAD)",
    source="IBGE",
    kind='line',
    units='%',
    years=ANOS_PADRAO
)


# =============================================================================
# 7. INFLACAO
# =============================================================================
print("\n[7] Inflacao")

# IPCA Mensal (barras)
save_chart(
    sidra.read('ipca'),
    filename="ipca_mensal.png",
    title="IPCA (Variação Mensal)",
    source="IBGE",
    kind='bar',
    units='%',
    years=ANOS_PADRAO,
    y_origin='auto'
)

# IPCA 12m (linha)
save_chart(
    sidra.read('ipca_12m'),
    filename="ipca_12m.png",
    title="IPCA (Acumulado 12 meses)",
    source="IBGE",
    kind='line',
    units='%',
    years=ANOS_PADRAO
)


# =============================================================================
# 8. JUROS E CAMBIO
# =============================================================================
print("\n[8] Juros e Cambio")

# Cambio (linhas sobrepostas)
df_dolar = sgs.read('dolar_ptax')
df_euro = sgs.read('euro_ptax')
df_cambio = pd.concat([df_dolar, df_euro], axis=1)
df_cambio.columns = ['Dólar', 'Euro']
save_chart(
    df_cambio,
    filename="cambio.png",
    title="Taxa de Câmbio (PTAX)",
    source="BCB",
    kind='line',
    units='BRL',
    years=ANOS_PADRAO
)

# Selic (linha)
save_chart(
    sgs.read('selic'),
    filename="selic.png",
    title="Taxa Selic (Meta)",
    source="BCB",
    kind='line',
    units='%',
    years=ANOS_PADRAO
)


# =============================================================================
# RESUMO
# =============================================================================
print(f"\n{'='*50}")
print(f"Graficos gerados em: {charting.CHARTS_PATH}")
print(f"Total: {len(list(charting.CHARTS_PATH.glob('*.png')))} arquivos")
