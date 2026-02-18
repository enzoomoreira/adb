# Bloomberg Terminal

Dados de mercado financeiro via Bloomberg Terminal.

## Visao Geral

| Caracteristica | Valor |
|----------------|-------|
| Fonte | Bloomberg Terminal (via xbbg) |
| Dados | Series temporais de mercado financeiro |
| Categorias | Equities globais, equities Brasil, equity valuations, commodities, indices de inflacao |
| Requisito | Bloomberg Terminal ativo para coleta |

**Importante:** A coleta requer o Bloomberg Terminal aberto e conectado. A leitura de dados ja salvos funciona offline.

---

## Indicadores Disponiveis

### Global Equities

| Indicador | Nome | Descricao |
|-----------|------|-----------|
| `msci_acwi_mktcap` | MSCI ACWI - Market Cap | Capitalizacao de mercado global |
| `msci_acwi_pe` | MSCI ACWI - P/E Ratio | Multiplo preco/lucro global |
| `msci_acwi_dividend` | MSCI ACWI - Dividend Yield | Rendimento de dividendos global |

### Brasil Equities

| Indicador | Nome | Descricao |
|-----------|------|-----------|
| `ibov_points` | Ibovespa - Pontos | Indice Bovespa em pontos |
| `ibov_usd` | Ibovespa - USD | Indice Bovespa em dolares |
| `ifix` | IFIX | Indice de fundos imobiliarios |

### Equity Valuations

Metricas de valuation (P/E forward e Dividend Yield) para indices globais. Podem ser lidas em grupo via constantes `GLOBAL_PE_FWD` e `GLOBAL_DY`.

| Indicador | Nome | Ticker | Campo |
|-----------|------|--------|-------|
| `cac_dy` | CAC 40 - DY | CAC Index | BEST_DIV_YLD |
| `cac_pe_fwd` | CAC 40 - P/E Fwd | CAC Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `dax_dy` | DAX - DY | DAX Index | BEST_DIV_YLD |
| `dax_pe_fwd` | DAX - P/E Fwd | DAX Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `dm_dy` | MSCI DM - DY | DM Index | BEST_DIV_YLD |
| `dm_pe_fwd` | MSCI DM - P/E Fwd | DM Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `ftsemib_pe_fwd` | FTSE MIB - P/E Fwd | FTSEMIB Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `ibov_dy` | Ibovespa - DY | IBOV Index | BEST_DIV_YLD |
| `ibov_pe_fwd` | Ibovespa - P/E Fwd | IBOV Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `ipsa_dy` | IPSA Chile - DY | IPSA Index | BEST_DIV_YLD |
| `jalsh_dy` | JSE All Share - DY | JALSH Index | BEST_DIV_YLD |
| `merval_dy` | MERVAL - DY | MERVAL Index | BEST_DIV_YLD |
| `merval_pe_fwd` | MERVAL - P/E Fwd | MERVAL Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `mexbol_dy` | IPC Mexico - DY | MEXBOL Index | BEST_DIV_YLD |
| `mexbol_pe_fwd` | IPC Mexico - P/E Fwd | MEXBOL Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `mxef_dy` | MSCI EM - DY | MXEF Index | BEST_DIV_YLD |
| `mxef_pe_fwd` | MSCI EM - P/E Fwd | MXEF Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `mxwo_pe_fwd` | MSCI World - P/E Fwd | MXWO Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `nky_dy` | Nikkei 225 - DY | NKY Index | BEST_DIV_YLD |
| `nky_pe_fwd` | Nikkei 225 - P/E Fwd | NKY Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `sensex_dy` | Sensex - DY | SENSEX Index | BEST_DIV_YLD |
| `sensex_pe_fwd` | Sensex - P/E Fwd | SENSEX Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `shcomp_dy` | Shanghai Comp - DY | SHCOMP Index | BEST_DIV_YLD |
| `shcomp_pe_fwd` | Shanghai Comp - P/E Fwd | SHCOMP Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `spx_dy` | S&P 500 - DY | SPX Index | BEST_DIV_YLD |
| `spx_pe_fwd` | S&P 500 - P/E Fwd | SPX Index | GEN_EST_PE_NEXT_YR_AGGTE |
| `ukx_dy` | FTSE 100 - DY | UKX Index | BEST_DIV_YLD |

### Commodities

| Indicador | Nome | Descricao |
|-----------|------|-----------|
| `brent` | Brent Crude | Petroleo Brent |
| `iron_ore` | Iron Ore | Minerio de ferro |
| `gold` | Gold Spot | Ouro spot |

### Indices de Inflacao

| Indicador | Nome | Descricao |
|-----------|------|-----------|
| `igpm` | IGPM-10 | Indice IGPM-10 FGV (mensal) |

---

## Exemplos de Uso

### Coletar Dados

```python
import adb

# Coleta todos os indicadores configurados
adb.bloomberg.collect()

# Coleta um indicador especifico
adb.bloomberg.collect(indicators='brent')

# Coleta multiplos indicadores
adb.bloomberg.collect(indicators=['brent', 'gold', 'ibov_points'])
```

A coleta e incremental: se ja existem dados salvos, apenas registros novos sao baixados.

### Leitura de Dados

```python
import adb

# Leitura simples
df = adb.bloomberg.read('brent')

# Leitura com filtro de data
df = adb.bloomberg.read('brent', start='2024-01-01')
df = adb.bloomberg.read('brent', start='2024', end='2024-06-30')

# Multiplos indicadores
df = adb.bloomberg.read('brent', 'gold')
df = adb.bloomberg.read('brent', 'gold', 'ibov_points', start='2024')
```

### Constantes de Grupo

Para leitura conjunta de metricas de valuation globais:

```python
from adb.providers.bloomberg.indicators import GLOBAL_PE_FWD, GLOBAL_DY
import adb

# P/E Forward de todas as bolsas (13 indices)
df_pe = adb.bloomberg.read(*GLOBAL_PE_FWD, start="2024")

# Dividend Yield de todas as bolsas (14 indices)
df_dy = adb.bloomberg.read(*GLOBAL_DY, start="2024")

# Coletar apenas valuations
adb.bloomberg.collect(GLOBAL_PE_FWD + GLOBAL_DY)
```

### Consultas e Status

```python
import adb

# Listar indicadores disponiveis
adb.bloomberg.available()
# ['brent', 'gold', 'ibov_points', ...]

# Filtrar por categoria
adb.bloomberg.available(category='commodities')
# ['brent', 'iron_ore', 'gold']

adb.bloomberg.available(category='equity_valuations')
# ['cac_dy', 'cac_pe_fwd', 'dax_dy', ..., 'ukx_dy']

# Informacoes de um indicador
adb.bloomberg.info('brent')
# {
#     'ticker': 'CO1 Comdty',
#     'fields': ['PX_LAST'],
#     'name': 'Brent Crude',
#     'frequency': 'daily',
#     'category': 'commodities'
# }

# Status dos arquivos salvos
adb.bloomberg.get_status()
```

---

## Arquivos Gerados

Apos a coleta, os dados sao salvos em:

```
data/raw/bloomberg/
    daily/
        msci_acwi_mktcap.parquet
        msci_acwi_pe.parquet
        msci_acwi_dividend.parquet
        ibov_points.parquet
        ibov_usd.parquet
        ibov_dy.parquet
        ifix.parquet
        brent.parquet
        iron_ore.parquet
        gold.parquet
        cac_dy.parquet
        cac_pe_fwd.parquet
        ...  (26 indicadores de equity valuations)
    monthly/
        igpm.parquet
```

Cada arquivo contem a serie temporal completa do indicador.

---

## Notas Importantes

### Requisitos para Coleta

1. **Bloomberg Terminal** instalado e ativo (licenca necessaria)
2. Terminal **aberto e conectado** durante a coleta
3. Pacote `xbbg` instalado

Se voce nao tem acesso ao Bloomberg Terminal, pode usar os dados ja coletados (leitura funciona offline).

### Lookback Padrao

Por padrao, a coleta busca 6 anos de historico (2190 dias) para novos indicadores. Atualizacoes posteriores buscam apenas dados novos desde a ultima coleta.

### Funcionamento Offline

A **leitura** de dados ja salvos funciona sem conexao com o Bloomberg:

```python
import adb

# Funciona offline se os dados ja foram coletados
df = adb.bloomberg.read('brent')
```

Apenas a **coleta** requer o Terminal ativo:

```python
import adb

# Requer Bloomberg Terminal ativo
adb.bloomberg.collect('brent')
```
