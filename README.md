# agora-database

Coleta e armazenamento de dados economicos brasileiros. Suporta cinco fontes:

| Fonte | Modulo | Dados |
|-------|--------|-------|
| BCB - SGS | `src/bacen/sgs/` | Series temporais (Selic, CDI, IPCA, cambio) |
| BCB - Focus | `src/bacen/expectations/` | Expectativas de mercado |
| MTE - CAGED | `src/mte/caged/` | Microdados de emprego formal |
| IPEA | `src/ipea/` | Dados agregados de emprego |
| Bloomberg Terminal | `src/bloomberg/` | Dados de mercado financeiro |

## Instalacao

```bash
uv sync
```

## Uso Rapido

### Coleta de Dados

```python
from core.collectors import collect, available_sources

# Ver fontes disponiveis
available_sources()
# ['sgs', 'expectations', 'caged', 'ipea', 'bloomberg']

# Coleta completa
collect('sgs')
collect('expectations')
collect('caged')
collect('ipea')

# Coleta parcial
collect('sgs', indicators='selic')
collect('sgs', indicators=['selic', 'cdi'])
```

### Leitura de Dados (Explorers)

```python
from core.data import sgs, expectations, caged, ipea, bloomberg

# SGS - Series Temporais BCB
df = sgs.read('selic')                    # Leitura simples
df = sgs.read('selic', start='2020')      # Com filtro de data
df = sgs.read('selic', 'cdi')             # Multiplos indicadores
sgs.available()                           # Lista indicadores

# Expectations - Relatorio Focus
df = expectations.read('ipca_anual')
df = expectations.read('ipca_anual', start='2024')

# IPEA - Dados Agregados
df = ipea.read('caged_saldo')
df = ipea.read('taxa_desemprego')

# CAGED - Microdados
df = caged.read(year=2024, month=10)      # Mes especifico
df = caged.saldo_mensal(year=2024)        # Agregacao por mes
df = caged.saldo_por_uf(year=2024)        # Agregacao por UF
caged.available_periods()                 # Periodos disponiveis

# Bloomberg (requer terminal)
df = bloomberg.read('brent')
df = bloomberg.read('ibov_points', start='2024')
```

### Queries SQL Diretas (QueryEngine)

Para queries mais complexas, use o QueryEngine com DuckDB:

```python
from core.data import QueryEngine

qe = QueryEngine()

# Leitura com filtros pushdown
df = qe.read(
    'cagedmov_202410',
    subdir='mte/caged',
    columns=['uf', 'saldomovimentacao'],
    where="uf = 35"  # SP
)

# SQL arbitrario
df = qe.sql('''
    SELECT uf, SUM(saldomovimentacao) as saldo
    FROM '{raw}/mte/caged/cagedmov_2024*.parquet'
    GROUP BY uf
    ORDER BY saldo DESC
''')

# Media anual da Selic
df = qe.sql('''
    SELECT
        strftime(date, '%Y') as ano,
        AVG(value) as media_selic
    FROM '{raw}/bacen/sgs/daily/selic.parquet'
    GROUP BY ano
    ORDER BY ano
''')
```

### Status da Coleta

```python
from core.collectors import get_status

get_status('sgs')
get_status('caged')
get_status('expectations')
```

## Estrutura de Dados

```
data/
└── raw/                          # Dados brutos em Parquet
    ├── bacen/
    │   ├── sgs/
    │   │   ├── daily/            # selic.parquet, cdi.parquet...
    │   │   └── monthly/          # ibc_br_bruto.parquet...
    │   └── expectations/         # ipca_anual.parquet...
    ├── mte/
    │   └── caged/                # cagedmov_2024-01.parquet...
    ├── ipea/
    │   └── monthly/              # caged_saldo.parquet...
    └── bloomberg/
        └── daily/                # brent.parquet, ibov_points.parquet...
```

## Indicadores Disponiveis

### SGS (Series Temporais)
- `selic`, `cdi`, `dolar_ptax`, `euro_ptax` (diarios)
- `ibc_br_bruto`, `ibc_br_dessaz`, `igp_m` (mensais)

### Expectations (Focus)
- `ipca_anual`, `igpm_anual`, `pib_anual`, `cambio_anual`, `selic_anual`
- `ipca_mensal`, `igpm_mensal`, `cambio_mensal`

### CAGED
- `cagedmov` - Movimentacoes (admissoes/desligamentos)
- `cagedfor` - Declaracoes fora do prazo
- `cagedexc` - Exclusoes

### IPEA
- `caged_saldo`, `caged_admissoes`, `caged_desligamentos`
- `taxa_desemprego`

### Bloomberg
- `msci_acwi_mktcap`, `msci_acwi_pe`, `msci_acwi_dividend` (global equities)
- `ibov_points`, `ibov_usd`, `ifix` (brasil equities)
- `brent`, `iron_ore`, `gold` (commodities)

## Extensibilidade

Adicione novos indicadores editando o arquivo `indicators.py` do modulo correspondente.

## Documentacao

Documentacao detalhada em `docs/`:

- [bacen.md](docs/bacen.md) - SGS e Expectations
- [mte.md](docs/mte.md) - CAGED (microdados)
- [ipea.md](docs/ipea.md) - Dados agregados IPEA
- [bloomberg.md](docs/bloomberg.md) - Dados de mercado
- [data.md](docs/data.md) - QueryEngine, DataManager, Explorers
- [utils.md](docs/utils.md) - BaseCollector, funcoes auxiliares
