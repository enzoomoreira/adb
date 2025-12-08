# agora-database

Coleta e armazenamento de dados economicos brasileiros. Suporta quatro fontes:

| Fonte | Modulo | Dados |
|-------|--------|-------|
| BCB - SGS | `src/bacen/sgs/` | Series temporais (Selic, CDI, IPCA, cambio) |
| BCB - Focus | `src/bacen/expectations/` | Expectativas de mercado |
| MTE - CAGED | `src/mte/caged/` | Microdados de emprego formal |
| IPEA | `src/ipea/` | Dados agregados de emprego |

## Instalacao

```bash
uv sync
```

## Uso Rapido

### BCB - Series Temporais (SGS)

```python
from src.bacen import SGSCollector

collector = SGSCollector('data/')

# Coleta
collector.collect()                      # Todos os indicadores
collector.collect('selic')               # Um indicador
collector.collect(['selic', 'cdi'])      # Lista

# Consolidacao (gera cdi_anualizado)
collector.consolidate()
```

### BCB - Expectativas Focus

```python
from src.bacen import ExpectationsCollector

collector = ExpectationsCollector('data/')
collector.collect()
collector.consolidate()
```

### MTE - CAGED (Microdados)

```python
from src.mte import CAGEDCollector

collector = CAGEDCollector('data/')

# Coleta (downloads paralelos)
collector.collect()

# Leitura com filtros
df = collector.read('cagedmov', year=2024)
df = collector.read('cagedmov', year=[2023, 2024], columns=['uf', 'saldomovimentacao'])

# Query SQL com DuckDB
df = collector.query('''
    SELECT uf, SUM(saldomovimentacao) as saldo
    FROM 'data/raw/mte/caged/cagedmov_*.parquet'
    GROUP BY uf
''')
```

### IPEA - Dados Agregados

```python
from src.ipea import IPEACollector

collector = IPEACollector('data/')
collector.collect()
collector.consolidate()
```

## Estrutura de Dados

```
data/
├── raw/                          # Dados brutos
│   ├── bacen/
│   │   ├── sgs/
│   │   │   ├── daily/            # selic, cdi, ptax
│   │   │   └── monthly/          # ibc-br, igp-m
│   │   └── expectations/         # expectativas Focus
│   ├── mte/
│   │   └── caged/                # microdados mensais
│   └── ipea/
│       └── monthly/              # dados agregados
└── processed/                    # Dados consolidados
```

## Indicadores Disponiveis

### SGS (Series Temporais)
- `selic`, `cdi`, `dolar_ptax`, `euro_ptax` (diarios)
- `ibc_br_bruto`, `ibc_br_dessaz`, `igp_m` (mensais)

### Expectations (Focus)
- `ipca_anual`, `igpm_anual`, `pib_anual`, `cambio_anual`, `selic_anual`
- `ipca_mensal`, `igpm_mensal`, `cambio_mensal`
- `selic`, `ipca_12m`, `ipca_24m`, `igpm_12m`

### CAGED
- `cagedmov` - Movimentacoes (admissoes/desligamentos)
- `cagedfor` - Declaracoes fora do prazo
- `cagedexc` - Exclusoes

### IPEA
- `caged_saldo`, `caged_admissoes`, `caged_desligamentos`
- `taxa_desemprego`

## Extensibilidade

Adicione novos indicadores editando o arquivo `indicators.py` do modulo:

```python
# src/bacen/sgs/indicators.py
SGS_CONFIG['novo'] = {'code': 12345, 'name': 'Nome', 'frequency': 'daily'}

# src/ipea/indicators.py
IPEA_CONFIG['novo'] = {'code': 'CODIGO_IPEA', 'name': 'Nome', 'frequency': 'monthly'}
```

## Documentacao

Documentacao detalhada em `docs/`:

- [architecture.md](docs/architecture.md) - Visao geral e estrutura
- [bacen.md](docs/bacen.md) - SGSCollector, ExpectationsCollector
- [mte.md](docs/mte.md) - CAGEDCollector, downloads paralelos
- [ipea.md](docs/ipea.md) - IPEACollector
- [data.md](docs/data.md) - DataManager, persistencia
- [utils.md](docs/utils.md) - ParallelFetcher, BaseCollector
