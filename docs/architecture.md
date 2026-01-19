# Arquitetura do Projeto agora-database

Visao geral da estrutura e funcionamento do repositorio.

## Visao Geral

Projeto para coleta e armazenamento de dados economicos brasileiros. Suporta cinco fontes de dados:

| Fonte | Modulo | Descricao | Docs |
|-------|--------|-----------|------|
| BCB - SGS | `src/bacen/sgs/` | Series temporais (Selic, CDI, IPCA, cambio) | [bacen.md](bacen.md) |
| BCB - Focus | `src/bacen/expectations/` | Expectativas de mercado | [bacen.md](bacen.md) |
| MTE - CAGED | `src/mte/caged/` | Microdados de emprego formal | [mte.md](mte.md) |
| IPEA | `src/ipea/` | Dados agregados de emprego | [ipea.md](ipea.md) |
| Bloomberg Terminal | `src/bloomberg/` | Dados de mercado financeiro | [bloomberg.md](bloomberg.md) |

---

## Estrutura de Pastas

```
agora-database/
├── src/
│   ├── core/                     # Modulo central
│   │   ├── __init__.py           # API publica centralizada
│   │   ├── config.py             # PROJECT_ROOT, DATA_PATH
│   │   ├── collectors/           # Sistema de coleta
│   │   │   ├── __init__.py       # collect, available_sources, get_status
│   │   │   ├── base.py           # BaseCollector
│   │   │   └── registry.py       # Registro de collectors
│   │   ├── data/                 # Persistencia e queries
│   │   │   ├── __init__.py       # DataManager, QueryEngine, explorers
│   │   │   ├── storage.py        # DataManager (persistencia)
│   │   │   └── query.py          # QueryEngine (consultas SQL)
│   │   └── utils/                # Utilitarios
│   │       ├── __init__.py       # Exports centralizados
│   │       ├── indicators.py     # list_indicators, get_indicator_config
│   │       └── dates.py          # parse_date, normalize_date_index
│   ├── bacen/                    # Modulo BCB
│   │   ├── __init__.py           # SGS_CONFIG, EXPECTATIONS_CONFIG
│   │   ├── sgs/                  # Series temporais SGS
│   │   │   ├── client.py         # SGSClient
│   │   │   ├── collector.py      # SGSCollector
│   │   │   ├── explorer.py       # SGSExplorer
│   │   │   └── indicators.py     # SGS_CONFIG
│   │   └── expectations/         # Expectativas Focus
│   │       ├── client.py         # ExpectationsClient
│   │       ├── collector.py      # ExpectationsCollector
│   │       ├── explorer.py       # ExpectationsExplorer
│   │       └── indicators.py     # EXPECTATIONS_CONFIG
│   ├── mte/                      # Modulo MTE
│   │   ├── __init__.py           # CAGED_CONFIG
│   │   └── caged/                # Microdados CAGED
│   │       ├── client.py         # CAGEDClient (FTP)
│   │       ├── collector.py      # CAGEDCollector
│   │       ├── explorer.py       # CAGEDExplorer
│   │       └── indicators.py     # CAGED_CONFIG
│   ├── ipea/                     # Modulo IPEA
│   │   ├── __init__.py           # IPEA_CONFIG
│   │   ├── client.py             # IPEAClient
│   │   ├── collector.py          # IPEACollector
│   │   ├── explorer.py           # IPEAExplorer
│   │   └── indicators.py         # IPEA_CONFIG
│   └── bloomberg/                # Modulo Bloomberg Terminal
│       ├── __init__.py           # BLOOMBERG_CONFIG
│       ├── client.py             # BloombergClient
│       ├── collector.py          # BloombergCollector
│       ├── explorer.py           # BloombergExplorer
│       └── indicators.py         # BLOOMBERG_CONFIG
├── data/                         # Dados coletados
│   ├── raw/                      # Dados brutos
│   │   ├── bacen/
│   │   │   ├── sgs/
│   │   │   │   ├── daily/        # selic, cdi, ptax
│   │   │   │   └── monthly/      # ibc-br, igp-m
│   │   │   └── expectations/     # expectativas Focus
│   │   ├── mte/
│   │   │   └── caged/            # microdados mensais
│   │   ├── ipea/
│   │   │   └── monthly/          # dados agregados
│   │   └── bloomberg/
│   │       └── daily/            # dados do Bloomberg Terminal
│   └── processed/                # Dados consolidados
├── notebooks/                    # Jupyter notebooks
├── scripts/                      # Scripts utilitarios
└── docs/                         # Documentacao
```

---

## Hierarquia de Classes

```
BaseCollector (src/core/collectors/base.py)
├── SGSCollector (src/bacen/sgs/collector.py)
├── ExpectationsCollector (src/bacen/expectations/collector.py)
├── CAGEDCollector (src/mte/caged/collector.py)
├── IPEACollector (src/ipea/collector.py)
└── BloombergCollector (src/bloomberg/collector.py)

# Persistencia (usado por collectors)
DataManager (src/core/data/storage.py)    # save/read/append/consolidate

# Consultas (usado para leitura/analise)
QueryEngine (src/core/data/query.py)      # SQL queries via DuckDB

# Utilitarios
core.utils.indicators (src/core/utils/indicators.py)  # list_indicators(), get_indicator_config()

# Explorers (interface pythonica para queries)
SGSExplorer (src/bacen/sgs/explorer.py)
ExpectationsExplorer (src/bacen/expectations/explorer.py)
CAGEDExplorer (src/mte/caged/explorer.py)
IPEAExplorer (src/ipea/explorer.py)
BloombergExplorer (src/bloomberg/explorer.py)
```

**Separacao de Responsabilidades:**
- **Collectors**: Apenas coleta de dados (collect, consolidate, get_status)
- **DataManager**: Persistencia (save, read, append)
- **QueryEngine**: Consultas SQL eficientes (sql, read, read_glob, aggregate)

---

## Fluxo de Dados

```
    API BCB         API Focus         FTP MTE         API IPEA      Bloomberg Terminal
    (SGS)          (Expectations)     (CAGED)        (ipeadatapy)        (xbbg)
        │                │                │                │                │
        ▼                ▼                ▼                ▼                ▼
   SGSClient    ExpectationsClient   CAGEDClient      IPEAClient     BloombergClient
        │                │                │                │                │
        ▼                ▼                ▼                ▼                ▼
   SGSCollector ExpectationsCollector CAGEDCollector IPEACollector BloombergCollector
        │                │                │                │                │
        └────────────────┴────────────────┴────────────────┴────────────────┘
                                            │
                                            ▼
                                      DataManager (storage.py)
                                            │
                            ┌───────────────┴───────────────┐
                            ▼                               ▼
                    data/raw/{subdir}/*.parquet    data/processed/*.parquet
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              Explorers      QueryEngine      DataManager.read()
           (interface        (SQL direto)     (leitura basica)
            pythonica)
```

---

## Padrao de Uso

### API Publica

Todos os collectors seguem o mesmo padrao:

```python
results = collector.collect('selic')              # Um indicador
results = collector.collect(['selic', 'cdi'])     # Lista
results = collector.collect()                      # Todos (default)
```

### Coleta Centralizada (Recomendado)

```python
from core.collectors import collect, available_sources, get_status

# Listar fontes disponiveis
available_sources()  # ['sgs', 'expectations', 'caged', 'ipea', 'bloomberg']

# Coleta (incremental automatico)
collect('sgs')
collect('sgs', indicators='selic')
collect('sgs', indicators=['selic', 'cdi'])

# Status dos dados
status = get_status('sgs')
```

### Leitura via Explorers (Recomendado)

Interface pythonica para leitura de dados coletados:

```python
from core.data import sgs, caged, expectations, ipea, bloomberg

# Leitura simples
df = sgs.read('selic')
df = sgs.read('selic', start='2020', end='2023')
df = sgs.read('selic', 'cdi')  # Multiplos indicadores

# CAGED (microdados)
df = caged.read(year=2025)
df = caged.read(year=2025, uf=35)

# Listar indicadores disponiveis
sgs.available()
sgs.info('selic')
```

### Leitura via QueryEngine (SQL Direto)

Para queries mais complexas, use o `QueryEngine`:

```python
from core.data import QueryEngine

qe = QueryEngine()

# Leitura simples
df = qe.read('selic', 'bacen/sgs/daily')

# Leitura com filtros
df = qe.read('selic', 'bacen/sgs/daily', columns=['value'], where="value > 10")

# Query SQL (suporta glob patterns e variaveis {raw}, {processed})
df = qe.sql('''
    SELECT strftime(date, '%Y') as ano, AVG(value) as media
    FROM '{raw}/bacen/sgs/daily/selic.parquet'
    GROUP BY ano
''')

# Leitura de multiplos arquivos (ideal para CAGED)
df = qe.read_glob('cagedmov_2024-*.parquet', subdir='mte/caged')
```

---

## Documentacao Detalhada

| Documento | Conteudo |
|-----------|----------|
| [bacen.md](bacen.md) | SGSCollector, ExpectationsCollector, configs |
| [mte.md](mte.md) | CAGEDCollector, downloads paralelos, query SQL |
| [ipea.md](ipea.md) | IPEACollector, dados agregados |
| [data.md](data.md) | DataManager, fetch_and_sync, persistencia |
| [utils.md](utils.md) | BaseCollector, funcoes auxiliares, registry |

---

## Formato de Dados

- **Formato**: Parquet (compressao Snappy)
- **Indice**: DatetimeIndex para series temporais
- **Coluna de valor**: `value` (normalizado pelos clients)

---

## Extensibilidade

Para adicionar novo indicador, editar o arquivo `indicators.py` do modulo correspondente:

```python
# src/bacen/sgs/indicators.py
SGS_CONFIG['novo_indicador'] = {
    'code': 12345,
    'name': 'Nome do Indicador',
    'frequency': 'daily',
}

# src/bacen/expectations/indicators.py
EXPECTATIONS_CONFIG['novo_indicador'] = {
    'endpoint': 'top5_anuais',
    'indicator': 'Nome na API',
}

# src/mte/caged/indicators.py
CAGED_CONFIG['novo_tipo'] = {
    'prefix': 'PREFIXO',
    'name': 'Nome',
    'start_year': 2020,
}

# src/ipea/indicators.py
IPEA_CONFIG['novo_indicador'] = {
    'code': 'CODIGO_IPEA',
    'name': 'Nome',
    'frequency': 'monthly',
}
```

---

## Comparacao de Collectors

| Aspecto | SGS/Expectations | CAGED | IPEA | Bloomberg |
|---------|------------------|-------|------|-----------|
| Protocolo | HTTP (REST) | FTP + 7z | HTTP (ipeadatapy) | Bloomberg Terminal (xbbg) |
| Volume/periodo | ~KB | ~500MB-1GB | ~KB | ~KB-MB |
| Retorno collect() | DataFrame | int (contagem) | DataFrame | DataFrame |
| Heranca | BaseCollector | BaseCollector | BaseCollector | BaseCollector |
