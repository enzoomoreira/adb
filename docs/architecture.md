# Arquitetura do Projeto dados-bcb

Visao geral da estrutura e funcionamento do repositorio.

## Visao Geral

Projeto para coleta e armazenamento de dados economicos brasileiros. Suporta quatro fontes de dados:

| Fonte | Modulo | Descricao | Docs |
|-------|--------|-----------|------|
| BCB - SGS | `src/bacen/sgs/` | Series temporais (Selic, CDI, IPCA, cambio) | [bacen.md](bacen.md) |
| BCB - Focus | `src/bacen/expectations/` | Expectativas de mercado | [bacen.md](bacen.md) |
| MTE - CAGED | `src/mte/caged/` | Microdados de emprego formal | [mte.md](mte.md) |
| IPEA | `src/ipea/` | Dados agregados de emprego | [ipea.md](ipea.md) |

---

## Estrutura de Pastas

```
dados-bcb/
├── src/
│   ├── bacen/                    # Modulo BCB
│   │   ├── base.py               # BaseCollector (classe base)
│   │   ├── sgs/                  # Series temporais SGS
│   │   │   ├── client.py         # SGSClient
│   │   │   ├── collector.py      # SGSCollector
│   │   │   └── indicators.py     # SGS_CONFIG
│   │   └── expectations/         # Expectativas Focus
│   │       ├── client.py         # ExpectationsClient
│   │       ├── collector.py      # ExpectationsCollector
│   │       └── indicators.py     # EXPECTATIONS_CONFIG
│   ├── mte/                      # Modulo MTE
│   │   └── caged/                # Microdados CAGED
│   │       ├── client.py         # CAGEDClient (FTP)
│   │       ├── collector.py      # CAGEDCollector
│   │       └── indicators.py     # CAGED_CONFIG
│   ├── ipea/                     # Modulo IPEA
│   │   ├── client.py             # IPEAClient
│   │   ├── collector.py          # IPEACollector
│   │   └── indicators.py         # IPEA_CONFIG
│   ├── core/                     # Utilitarios compartilhados
│   │   └── parallel.py           # ParallelFetcher
│   └── data/
│       └── manager.py            # DataManager
├── data/                         # Dados coletados
│   ├── raw/                      # Dados brutos
│   │   ├── bacen/
│   │   │   ├── sgs/
│   │   │   │   ├── daily/        # selic, cdi, ptax
│   │   │   │   └── monthly/      # ibc-br, igp-m
│   │   │   └── expectations/     # expectativas Focus
│   │   ├── mte/
│   │   │   └── caged/            # microdados mensais
│   │   └── ipea/
│   │       └── monthly/          # dados agregados
│   └── processed/                # Dados consolidados
├── notebooks/                    # Jupyter notebooks
├── scripts/                      # Scripts utilitarios
└── docs/                         # Documentacao
```

---

## Hierarquia de Classes

```
BaseCollector (src/bacen/base.py)
├── SGSCollector (src/bacen/sgs/collector.py)
└── ExpectationsCollector (src/bacen/expectations/collector.py)

CAGEDCollector (src/mte/caged/collector.py)  # Independente
IPEACollector (src/ipea/collector.py)        # Independente

DataManager (src/data/manager.py)  # Usado por todos os collectors
ParallelFetcher (src/core/parallel.py)  # Usado pelo CAGEDCollector
```

---

## Fluxo de Dados

```
    API BCB          API Focus          FTP MTE           API IPEA
    (SGS)           (Expectations)      (CAGED)          (ipeadatapy)
        │                  │                │                  │
        ▼                  ▼                ▼                  ▼
   SGSClient      ExpectationsClient   CAGEDClient       IPEAClient
        │                  │                │                  │
        ▼                  ▼                ▼                  ▼
   SGSCollector   ExpectationsCollector CAGEDCollector   IPEACollector
        │                  │                │                  │
        └──────────────────┴────────────────┴──────────────────┘
                                    │
                                    ▼
                             DataManager
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            data/raw/{subdir}/*.parquet    data/processed/*.parquet
```

---

## Padrao de Uso

### API de Dois Niveis

Todos os collectors seguem o mesmo padrao:

```python
# Nivel 1: Controle total
df = collector.collect_series(code=432, filename='selic', frequency='daily')

# Nivel 2: API simplificada
results = collector.collect('selic')              # Um indicador
results = collector.collect(['selic', 'cdi'])     # Lista
results = collector.collect()                      # Todos
```

### Coleta e Consolidacao

```python
from src.bacen import SGSCollector

collector = SGSCollector('data/')

# Coleta (incremental automatico)
collector.collect()

# Consolidacao
results = collector.consolidate()
```

---

## Documentacao Detalhada

| Documento | Conteudo |
|-----------|----------|
| [bacen.md](bacen.md) | SGSCollector, ExpectationsCollector, configs |
| [mte.md](mte.md) | CAGEDCollector, downloads paralelos, query SQL |
| [ipea.md](ipea.md) | IPEACollector, dados agregados |
| [data.md](data.md) | DataManager, fetch_and_sync, persistencia |
| [utils.md](utils.md) | ParallelFetcher, BaseCollector |

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

| Aspecto | SGS/Expectations | CAGED | IPEA |
|---------|------------------|-------|------|
| Protocolo | HTTP (REST) | FTP + 7z | HTTP (ipeadatapy) |
| Volume/periodo | ~KB | ~500MB-1GB | ~KB |
| Retorno collect() | DataFrame | int (contagem) | DataFrame |
| Parallelismo | Nao | Sim (threads) | Nao |
| Heranca | BaseCollector | Independente | Independente |
