# Utilitarios e Classes Base

Documentacao de componentes compartilhados do projeto.

---

## Visao Geral

O modulo `src/core/` contem os componentes centralizados do projeto:

| Componente | Localizacao | Descricao |
|------------|-------------|-----------|
| Funcoes de indicadores | `core/utils/indicators.py` | Manipulacao de configs |
| Funcoes de datas | `core/utils/dates.py` | Parsing e normalizacao (parse_date, normalize_date_index) |
| BaseCollector | `core/collectors/base.py` | Classe base para collectors |
| Registry | `core/collectors/registry.py` | Interface centralizada de coleta |
| Config | `core/config.py` | Configuracao global (paths) |

---

## core.utils (Funcoes Auxiliares)

### Funcoes de Indicadores

**Localizacao:** `src/core/utils/indicators.py`

```python
from core import list_indicators, get_indicator_config, filter_by_field
# ou
from core.utils import list_indicators, get_indicator_config, filter_by_field
```

> **Nota:** Funcoes de datas (`parse_date`, `normalize_date_index`) tambem estao disponiveis em `core.utils` mas sao de uso interno.

#### list_indicators(config, frequency=None)

Lista chaves de indicadores disponiveis em uma configuracao.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| config | dict | Dicionario de configuracao (ex: SGS_CONFIG) |
| frequency | str | Filtrar por frequencia (opcional) |

**Retorno:** list[str]

```python
from core import list_indicators
from src.bacen import SGS_CONFIG

keys = list_indicators(SGS_CONFIG)
# ['selic', 'cdi', 'dolar_ptax', 'euro_ptax', ...]

daily_keys = list_indicators(SGS_CONFIG, frequency='daily')
# ['selic', 'cdi', 'dolar_ptax', 'euro_ptax']
```

#### get_indicator_config(config, key)

Obtem a configuracao completa de um indicador.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| config | dict | Dicionario de configuracao |
| key | str | Chave do indicador |

**Retorno:** dict

```python
from core import get_indicator_config
from src.bacen import SGS_CONFIG

cfg = get_indicator_config(SGS_CONFIG, 'selic')
# {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily'}

# Erro se indicador nao existe:
cfg = get_indicator_config(SGS_CONFIG, 'invalido')
# KeyError: "Indicador 'invalido' nao encontrado. Disponiveis: ..."
```

#### filter_by_field(config, field, value)

Filtra indicadores por valor de campo especifico.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| config | dict | Dicionario de configuracao |
| field | str | Campo para filtrar (ex: 'frequency') |
| value | any | Valor esperado do campo |

**Retorno:** dict (subconjunto da config original)

```python
from core import filter_by_field
from src.bacen import SGS_CONFIG

monthly = filter_by_field(SGS_CONFIG, 'frequency', 'monthly')
# {'ibc_br_bruto': {...}, 'ibc_br_dessaz': {...}, ...}
```

---

## core.collectors (Sistema de Coleta)

### Interface Centralizada (Registry)

**Localizacao:** `src/core/collectors/registry.py`

```python
from core.collectors import collect, available_sources, get_status
# ou
from core import collect, available_sources, get_status
```

#### collect(source, indicators='all', save=True, verbose=True, **kwargs)

Interface unificada para coleta de dados.

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| source | str | - | Fonte de dados ('sgs', 'expectations', 'caged', 'ipea', 'bloomberg') |
| indicators | str\|list | 'all' | Indicadores a coletar |
| save | bool | True | Salvar em Parquet |
| verbose | bool | True | Imprimir progresso |
| **kwargs | - | - | Argumentos extras (ex: max_workers para caged) |

```python
from core.collectors import collect

# Coleta completa
collect('sgs')
collect('expectations')
collect('caged')
collect('ipea')
collect('bloomberg')

# Coleta parcial
collect('sgs', indicators='selic')
collect('sgs', indicators=['selic', 'cdi'])

# Com parametros extras (CAGED)
collect('caged', year=2025)
collect('caged', year=2025, month=10)
collect('caged', year=2025, parallel=True, max_workers=4)
```

#### available_sources()

Lista fontes de dados disponiveis.

**Retorno:** list[str]

```python
from core.collectors import available_sources

sources = available_sources()
# ['sgs', 'expectations', 'caged', 'ipea', 'bloomberg']
```

#### get_status(source)

Retorna status dos dados de uma fonte.

**Retorno:** pd.DataFrame ou dict

```python
from core.collectors import get_status

status = get_status('sgs')
status = get_status('caged')
```

---

## BaseCollector

Classe base para todos os coletores do projeto.

**Localizacao:** `src/core/collectors/base.py`

### Visao Geral

Fornece funcionalidades comuns herdadas por todos os collectors:
- Delegacoes para DataManager
- Logging padronizado
- Metodo `get_status()` unificado
- Inicializacao padronizada

**Collectors que herdam BaseCollector:**
- SGSCollector
- ExpectationsCollector
- CAGEDCollector
- IPEACollector
- BloombergCollector

### Atributos de Configuracao

Subclasses devem definir:

```python
class SGSCollector(BaseCollector):
    default_subdir = 'bacen/sgs/daily'
```

| Atributo | Tipo | Descricao |
|----------|------|-----------|
| default_subdir | str | Subdiretorio padrao para operacoes |

### Metodos Publicos

#### get_status(subdir=None)

Retorna DataFrame com status de cada arquivo:

| Coluna | Descricao |
|--------|-----------|
| arquivo | Nome do arquivo |
| subdir | Subdiretorio |
| registros | Numero de linhas |
| colunas | Numero de colunas |
| primeira_data | Data inicial |
| ultima_data | Data final |
| status | 'OK' ou 'Vazio' |

### Metodos Helper (Internos)

Metodos com prefixo `_` que padronizam comportamentos comuns:

#### _normalize_indicators_list(indicators, config)

Normaliza entrada de indicadores para lista.

- `'all'` -> retorna todas as chaves da config
- `'selic'` -> retorna `['selic']`
- `['selic', 'cdi']` -> retorna como esta

#### _log_collect_start(title, num_indicators, subdir=None, check_first_run=False, verbose=True)

Imprime banner padronizado de inicio de coleta.

```
======================================================================
PRIMEIRA EXECUCAO - Download de Historico Completo
======================================================================
BACEN - Sistema Gerenciador de Series
======================================================================
Indicadores a coletar: 7
```

#### _log_collect_end(results, verbose=True)

Imprime banner padronizado de fim de coleta.

```
======================================================================
Coleta concluida! Total: 1,523 registros
======================================================================
```

#### _log_fetch_start(name, start_date=None, verbose=True)

Log de inicio de busca de um indicador.

```
  Buscando SELIC desde 2024-01-01...
  Buscando SELIC (historico completo)...
```

#### _log_fetch_result(name, count, verbose=True)

Log de resultado de busca.

```
  252 registros
  Sem dados disponiveis
```

#### _calculate_start_date(last_date, frequency)

Calcula data inicial para coleta incremental baseada na ultima data salva.

- `frequency='monthly'`: retorna primeiro dia do proximo mes
- `frequency='daily'` (ou outro): retorna proximo dia

#### _collect_with_sync(fetch_fn, filename, name, subdir, frequency='daily', save=True, verbose=True)

Template pattern para coleta com suporte a atualizacao incremental.

---

## core.config

**Localizacao:** `src/core/config.py`

Configuracao global do projeto.

```python
from core import PROJECT_ROOT, DATA_PATH
# ou
from core.config import PROJECT_ROOT, DATA_PATH

print(PROJECT_ROOT)  # Path do diretorio raiz do projeto
print(DATA_PATH)     # Path do diretorio de dados (default: data/)
```

---

## Estrutura de Modulos

```
src/
├── core/
│   ├── __init__.py           # API centralizada
│   ├── config.py             # PROJECT_ROOT, DATA_PATH
│   ├── collectors/
│   │   ├── __init__.py       # collect, available_sources, get_status, BaseCollector
│   │   ├── base.py           # BaseCollector
│   │   └── registry.py       # Funcoes de registro
│   ├── data/
│   │   ├── __init__.py       # DataManager, QueryEngine, Explorers
│   │   ├── storage.py        # DataManager
│   │   └── query.py          # QueryEngine
│   └── utils/
│       ├── __init__.py       # list_indicators, get_indicator_config, filter_by_field, parse_date, normalize_date_index
│       ├── indicators.py     # Funcoes de indicadores
│       └── dates.py          # Funcoes de datas (parse_date, normalize_date_index)
├── bacen/
│   ├── __init__.py           # SGS_CONFIG, EXPECTATIONS_CONFIG
│   ├── sgs/
│   │   ├── client.py         # SGSClient
│   │   ├── collector.py      # SGSCollector
│   │   ├── explorer.py       # SGSExplorer
│   │   └── indicators.py     # SGS_CONFIG
│   └── expectations/
│       ├── client.py         # ExpectationsClient
│       ├── collector.py      # ExpectationsCollector
│       ├── explorer.py       # ExpectationsExplorer
│       └── indicators.py     # EXPECTATIONS_CONFIG
├── mte/
│   ├── __init__.py           # CAGED_CONFIG
│   └── caged/
│       ├── client.py         # CAGEDClient
│       ├── collector.py      # CAGEDCollector
│       ├── explorer.py       # CAGEDExplorer
│       └── indicators.py     # CAGED_CONFIG
├── ipea/
│   ├── __init__.py           # IPEA_CONFIG
│   ├── client.py             # IPEAClient
│   ├── collector.py          # IPEACollector
│   ├── explorer.py           # IPEAExplorer
│   └── indicators.py         # IPEA_CONFIG
└── bloomberg/
    ├── __init__.py           # BLOOMBERG_CONFIG
    ├── client.py             # BloombergClient
    ├── collector.py          # BloombergCollector
    ├── explorer.py           # BloombergExplorer
    └── indicators.py         # BLOOMBERG_CONFIG
```

---

## Hierarquia de Collectors

```
BaseCollector (src/core/collectors/base.py)
├── SGSCollector (src/bacen/sgs/collector.py)
├── ExpectationsCollector (src/bacen/expectations/collector.py)
├── CAGEDCollector (src/mte/caged/collector.py)
├── IPEACollector (src/ipea/collector.py)
└── BloombergCollector (src/bloomberg/collector.py)
```

---

## Imports Centralizados

```python
# Interface de coleta (recomendado)
from core.collectors import collect, available_sources, get_status

# Leitura de dados (recomendado)
from core.data import sgs, expectations, caged, ipea, bloomberg

# Componentes de dados
from core.data import DataManager, QueryEngine

# Funcoes auxiliares
from core import list_indicators, get_indicator_config, filter_by_field

# Funcoes de datas (uso interno)
from core.utils import parse_date, normalize_date_index

# Configuracao
from core import PROJECT_ROOT, DATA_PATH

# Configs de indicadores (para referencia)
from bacen import SGS_CONFIG, EXPECTATIONS_CONFIG
from mte import CAGED_CONFIG
from ipea import IPEA_CONFIG
from bloomberg import BLOOMBERG_CONFIG
```
