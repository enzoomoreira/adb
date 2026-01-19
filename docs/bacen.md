# Modulo BCB (Banco Central do Brasil)

Documentacao dos coletores de dados do Banco Central: SGS e Expectations.

## Visao Geral

O modulo `src/bacen/` contem dois coletores principais:

| Coletor | Fonte | Descricao |
|---------|-------|-----------|
| SGSCollector | API SGS | Series temporais (Selic, CDI, IPCA, cambio, etc) |
| ExpectationsCollector | API Focus | Expectativas de mercado (relatorio Focus) |

---

## Arquitetura de Uso

O projeto usa uma arquitetura centralizada. Os modulos internos (`src/bacen/`, `src/ipea/`, etc) nao exportam Collectors/Clients diretamente.

### Para Coleta de Dados

```python
from core.collectors import collect

# Coleta SGS
collect('sgs')                           # Todos indicadores
collect('sgs', indicators='selic')       # Um indicador
collect('sgs', indicators=['selic', 'cdi'])  # Lista

# Coleta Expectations
collect('expectations')                  # Todos
collect('expectations', indicators='ipca_anual')
```

### Para Leitura/Queries (Explorers)

```python
from core.data import sgs, expectations

# SGS Explorer
df = sgs.read('selic')                   # Leitura simples
df = sgs.read('selic', start='2020')     # Com filtro de data
df = sgs.read('selic', 'cdi')            # Multiplos indicadores
print(sgs.available())                   # Lista indicadores disponiveis
print(sgs.info('selic'))                 # Info do indicador

# Expectations Explorer
df = expectations.read('ipca_anual')
df = expectations.read('ipca_anual', start='2024')
print(expectations.available())
```

---

## SGS_CONFIG

Indicadores disponiveis em `src/bacen/sgs/indicators.py`:

**Diarios:** `selic`, `cdi`, `dolar_ptax`, `euro_ptax`

**Mensais:** `ibc_br_bruto`, `ibc_br_dessaz`, `igp_m`, ...

### Funcoes Auxiliares

```python
from src.bacen import SGS_CONFIG
from core import list_indicators, get_indicator_config, filter_by_field

list_indicators(SGS_CONFIG)                        # Lista chaves
get_indicator_config(SGS_CONFIG, 'selic')          # Config do indicador
filter_by_field(SGS_CONFIG, 'frequency', 'daily')  # Filtra por frequencia
```

---

## EXPECTATIONS_CONFIG

Indicadores disponiveis em `src/bacen/expectations/indicators.py`:

**Anuais (Top 5 previsores):**
| Chave | Endpoint | Indicador |
|-------|----------|-----------|
| ipca_anual | top5_anuais | IPCA |
| igpm_anual | top5_anuais | IGP-M |
| pib_anual | top5_anuais | PIB Total |
| cambio_anual | top5_anuais | Cambio |
| selic_anual | top5_anuais | Selic |

**Mensais:**
| Chave | Endpoint | Indicador |
|-------|----------|-----------|
| ipca_mensal | mensais | IPCA |
| igpm_mensal | mensais | IGP-M |
| cambio_mensal | mensais | Cambio |

**Selic e Inflacao:**
| Chave | Endpoint | Indicador |
|-------|----------|-----------|
| selic | selic | Selic |
| ipca_12m | inflacao_12m | IPCA |
| ipca_24m | inflacao_24m | IPCA |
| igpm_12m | inflacao_12m | IGP-M |

---

## Uso Avancado (Acesso Direto)

Para casos especiais onde e necessario acesso direto aos collectors/clients:

```python
# Collectors (imports diretos - uso interno)
from bacen.sgs.collector import SGSCollector
from bacen.expectations.collector import ExpectationsCollector

collector = SGSCollector(data_path='data/')
results = collector.collect('selic')
collector.get_status()

# Clients (baixo nivel)
from bacen.sgs.client import SGSClient
from bacen.expectations.client import ExpectationsClient

client = SGSClient()
df = client.get_data(code=432, name='Selic', frequency='daily', start_date='2024-01-01')
```

### SGSCollector.collect()

```python
def collect(
    indicators: list[str] | str = 'all',
    save: bool = True,
    verbose: bool = True,
) -> dict[str, pd.DataFrame]
```

### ExpectationsCollector.collect()

```python
def collect(
    indicators: list[str] | str = 'all',
    start_date: str = None,
    limit: int = None,
    save: bool = True,
    verbose: bool = True,
) -> dict[str, pd.DataFrame]
```

---

## Exports Publicos

```python
# Configs (exportados)
from src.bacen import SGS_CONFIG, EXPECTATIONS_CONFIG

# Funcoes auxiliares (centralizadas em core)
from core import (
    list_indicators,
    get_indicator_config,
    filter_by_field,
)

# Interface centralizada (recomendado)
from core.collectors import collect, available_sources, get_status
from core.data import sgs, expectations
```

---

## Arquivos Gerados

```
data/
└── raw/
    └── bacen/
        ├── sgs/
        │   ├── daily/        # selic.parquet, cdi.parquet, etc
        │   └── monthly/      # ibc_br_bruto.parquet, igp_m.parquet, etc
        └── expectations/     # ipca_anual.parquet, selic.parquet, etc
```
