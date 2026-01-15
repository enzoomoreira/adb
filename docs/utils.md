# Utilitarios e Classes Base

Documentacao de componentes compartilhados do projeto.

---

## core.indicators

Funcoes centralizadas para manipulacao de indicadores.

**Localizacao:** `src/core/indicators.py`

### Visao Geral

Modulo com funcoes genericas para trabalhar com configuracoes de indicadores, eliminando duplicacao de codigo entre modulos (bacen, ipea, mte, bloomberg).

**Funcoes disponiveis:**
- `list_indicators(config)` - Lista chaves de indicadores
- `get_indicator_config(config, key)` - Obtem configuracao de um indicador
- `filter_by_field(config, field, value)` - Filtra indicadores por campo

### list_indicators(config, frequency=None)

Lista chaves de indicadores disponiveis em uma configuracao.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| config | dict | Dicionario de configuracao (ex: SGS_CONFIG) |
| frequency | str | Filtrar por frequencia (opcional) |

**Retorno:** list[str]

**Exemplo:**
```python
from core.indicators import list_indicators
from bacen.sgs import SGS_CONFIG

# Todos os indicadores
keys = list_indicators(SGS_CONFIG)
# ['selic', 'cdi', 'dolar_ptax', 'euro_ptax', ...]

# Apenas diarios
daily_keys = list_indicators(SGS_CONFIG, frequency='daily')
# ['selic', 'cdi', 'dolar_ptax', 'euro_ptax']
```

### get_indicator_config(config, key)

Obtem a configuracao completa de um indicador.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| config | dict | Dicionario de configuracao |
| key | str | Chave do indicador |

**Retorno:** dict

**Exemplo:**
```python
from core.indicators import get_indicator_config
from bacen.sgs import SGS_CONFIG

cfg = get_indicator_config(SGS_CONFIG, 'selic')
# {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily'}
```

### filter_by_field(config, field, value)

Filtra indicadores por valor de campo especifico.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| config | dict | Dicionario de configuracao |
| field | str | Campo para filtrar (ex: 'frequency', 'name') |
| value | any | Valor esperado do campo |

**Retorno:** dict (subconjunto da config original)

**Exemplo:**
```python
from core.indicators import filter_by_field
from bacen.sgs import SGS_CONFIG

# Apenas indicadores mensais
monthly = filter_by_field(SGS_CONFIG, 'frequency', 'monthly')
# {'ibc_br_bruto': {...}, 'ibc_br_dessaz': {...}, 'igp_m': {...}}
```

### Import

```python
from core.indicators import (
    list_indicators,
    get_indicator_config,
    filter_by_field,
)
```

---

## ParallelFetcher

Executor paralelo generico para tarefas I/O-bound.

**Localizacao:** `src/core/parallel.py`

### Uso Basico

```python
from core.parallel import ParallelFetcher

# Inicializa com numero de threads
fetcher = ParallelFetcher(max_workers=4)

# Executa funcao em paralelo para cada item
results = fetcher.fetch_all(items, fetch_fn)
# Retorna: dict[item, resultado]
```

### Construtor

```python
ParallelFetcher(
    max_workers: int = 4,
    on_item_complete: Callable[[T, R], None] = None
)
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| max_workers | int | 4 | Numero maximo de threads |
| on_item_complete | Callable | None | Callback apos cada tarefa |

### fetch_all(items, fetch_fn)

Executa `fetch_fn` para cada item em paralelo.

```python
def fetch_all(
    items: Iterable[T],
    fetch_fn: Callable[[T], R]
) -> dict[T, R]
```

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| items | Iterable | Lista de itens para processar |
| fetch_fn | Callable | Funcao que processa um item |

**Retorno:** `dict[item, resultado]`

### Comportamentos

**Fallback sequencial:**
- Se `max_workers <= 1`, executa sequencialmente
- Util para debug

**Tratamento de erros:**
- Erros sao capturados e impressos
- Retorna `None` para itens com falha
- Continua processando outros itens

### Exemplo: Download Paralelo

```python
def download(url):
    response = requests.get(url)
    return response.content

fetcher = ParallelFetcher(max_workers=8)
results = fetcher.fetch_all(urls, download)

for url, content in results.items():
    if content is not None:
        save(url, content)
```

### Uso no Projeto

Usado pelo `CAGEDCollector` para downloads FTP paralelos:

```python
# Em src/mte/caged/collector.py
tasks = [(key, year, month, save, verbose) for year, month in missing]

def fetch_adapter(args):
    return self._fetch_single_period(*args)

fetcher = ParallelFetcher(max_workers=4)
batch_results = fetcher.fetch_all(tasks, fetch_adapter)

total_rows = sum(r for r in batch_results.values() if r is not None)
```

---

## BaseCollector

Classe base para todos os coletores do projeto.

**Localizacao:** `src/core/collectors/base.py`

### Visao Geral

Fornece funcionalidades comuns herdadas por todos os collectors do projeto:
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
    default_consolidate_subdirs = ['bacen/sgs/daily', 'bacen/sgs/monthly']
```

| Atributo | Tipo | Descricao |
|----------|------|-----------|
| default_subdir | str | Subdiretorio padrao para operacoes |
| default_consolidate_subdirs | list[str] | Subdiretorios para consolidacao |

### Metodos Herdados

#### save(df, filename, subdir=None, **kwargs)

Delega para `DataManager.save()`. Usa `default_subdir` se `subdir` nao especificado.

#### read(filename, subdir=None)

Delega para `DataManager.read()`. Retorna DataFrame vazio se arquivo nao existe.

#### list_files(subdir=None)

Delega para `DataManager.list_files()`. Retorna lista de nomes (sem extensao).

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

### Metodos de Logging

Usados internamente para output padronizado:

```python
# Inicio de busca
self._log_fetch_start('SELIC', start_date='2024-01-01', verbose=True)
# Output: "  Buscando SELIC desde 2024-01-01..."

self._log_fetch_start('SELIC', start_date=None, verbose=True)
# Output: "  Buscando SELIC (historico completo)..."

# Resultado
self._log_fetch_result('SELIC', count=252, verbose=True)
# Output: "  252 registros"

self._log_fetch_result('SELIC', count=0, verbose=True)
# Output: "  Sem dados disponiveis"
```

### Hierarquia

```
BaseCollector (src/core/collectors/base.py)
├── SGSCollector (src/bacen/sgs/collector.py)
├── ExpectationsCollector (src/bacen/expectations/collector.py)
├── CAGEDCollector (src/mte/caged/collector.py)
├── IPEACollector (src/ipea/collector.py)
└── BloombergCollector (src/bloomberg/collector.py)
```

**Nota:** Todos os collectors agora herdam de `BaseCollector` para aproveitar funcionalidades comuns como logging padronizado, delegacoes ao DataManager e metodo `get_status()`.

---

### Metodos Helper para Collectors

Metodos internos (prefixo `_`) que padronizam comportamentos comuns entre collectors.

#### _normalize_indicators_list(indicators, config)

Normaliza entrada de indicadores para lista.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| indicators | str\|list | 'all', lista ou string unica |
| config | dict | Dicionario de configuracao (ex: SGS_CONFIG) |

**Retorno:** list[str]

**Comportamento:**
- `'all'` → retorna todas as chaves da config
- `'selic'` → retorna `['selic']`
- `['selic', 'cdi']` → retorna como esta

**Exemplo:**
```python
# 'all' -> todas as chaves da config
keys = self._normalize_indicators_list('all', SGS_CONFIG)

# string -> lista com um elemento
keys = self._normalize_indicators_list('selic', SGS_CONFIG)

# lista -> mantem como lista
keys = self._normalize_indicators_list(['selic', 'cdi'], SGS_CONFIG)
```

#### _normalize_subdirs_list(subdirs)

Normaliza entrada de subdiretorios para lista.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| subdirs | str\|list\|None | None (usa default), string ou lista |

**Retorno:** list[str]

**Comportamento:**
- `None` → retorna `default_consolidate_subdirs`
- `'bacen/sgs/daily'` → retorna `['bacen/sgs/daily']`
- `['daily', 'monthly']` → retorna como esta

#### _log_collect_start(title, num_indicators, subdir=None, check_first_run=False, verbose=True)

Imprime banner padronizado de inicio de coleta.

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| title | str | - | Titulo (ex: "BACEN - SGS") |
| num_indicators | int | - | Numero de indicadores |
| subdir | str | None | Subdiretorio para checar first_run |
| check_first_run | bool | False | Mostrar "PRIMEIRA EXECUCAO" vs "ATUALIZACAO" |
| verbose | bool | True | Se False, nao imprime |

**Output exemplo:**
```
================================================================================
                           COLETA: BACEN - SGS
                         ATUALIZACAO | 7 indicadores
================================================================================
```

#### _log_collect_end(results, verbose=True)

Imprime banner padronizado de fim de coleta com total de registros.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| results | dict | Dicionario {key: DataFrame} |
| verbose | bool | Se False, nao imprime |

**Output exemplo:**
```
================================================================================
                        COLETA CONCLUIDA: 1,523 registros
================================================================================
```

#### _log_consolidate_start(title, subdir=None, verbose=True)

Imprime banner padronizado de inicio de consolidacao.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| title | str | Titulo (ex: "SGS Daily") |
| subdir | str | Subdiretorio sendo consolidado |
| verbose | bool | Se False, nao imprime |

**Output exemplo:**
```
--------------------------------------------------------------------------------
                       CONSOLIDANDO: SGS Daily
                       Subdir: bacen/sgs/daily
--------------------------------------------------------------------------------
```

#### _save_parquet_to_processed(df, filename, verbose=True)

Salva DataFrame no diretorio `processed/` como Parquet.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| df | DataFrame | Dados a salvar |
| filename | str | Nome do arquivo (sem extensao) |
| verbose | bool | Se True, imprime caminho |

**Retorno:** Path do arquivo salvo, ou None se df vazio

**Exemplo:**
```python
path = self._save_parquet_to_processed(df, 'sgs_daily_consolidated')
# Output: "  Salvo em: data/processed/sgs_daily_consolidated.parquet"
```

#### _collect_with_sync(fetch_fn, filename, name, subdir, frequency, save=True, verbose=True)

Template pattern para coleta com suporte a `fetch_and_sync`.

Padroniza o fluxo de coleta:
1. Cria wrapper para `fetch_fn` com logging
2. Usa `fetch_and_sync` se `save=True`
3. Loga resultado
4. Retorna DataFrame

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| fetch_fn | Callable | Funcao(start_date) -> DataFrame |
| filename | str | Nome do arquivo |
| name | str | Nome para logs |
| subdir | str | Subdiretorio em raw/ |
| frequency | str | 'daily', 'monthly', etc |
| save | bool | Se True, usa fetch_and_sync |
| verbose | bool | Imprimir logs |

**Retorno:** DataFrame coletado

**Exemplo de uso em collector:**
```python
def collect(self, indicators='all', save=True, verbose=True):
    keys = self._normalize_indicators_list(indicators, MY_CONFIG)
    self._log_collect_start("My Collector", len(keys), verbose=verbose)
    
    results = {}
    for key in keys:
        cfg = MY_CONFIG[key]
        df = self._collect_with_sync(
            fetch_fn=lambda sd: self.client.get(cfg['code'], start_date=sd),
            filename=key,
            name=cfg['name'],
            subdir=self.default_subdir,
            frequency=cfg['frequency'],
            save=save,
            verbose=verbose,
        )
        results[key] = df
    
    self._log_collect_end(results, verbose=verbose)
    return results
```

---

### Tabela Resumo: Metodos Helper

| Metodo | Usado Por | Proposito |
|--------|-----------|----------|
| `_normalize_indicators_list()` | Bloomberg, IPEA, Expectations, SGS | Normaliza entrada de indicadores |
| `_normalize_subdirs_list()` | Expectations, SGS | Normaliza entrada de subdirs |
| `_log_collect_start()` | Bloomberg, IPEA, Expectations, SGS | Banner de inicio |
| `_log_collect_end()` | Bloomberg, IPEA, Expectations, SGS | Banner de conclusao |
| `_log_consolidate_start()` | Bloomberg, IPEA, Expectations, SGS | Banner de consolidacao |
| `_save_parquet_to_processed()` | Expectations, SGS | Salva em processed/ |
| `_collect_with_sync()` | Bloomberg, IPEA, SGS | Template de coleta |

**Nota:** CAGEDCollector nao usa estes helpers devido ao seu fluxo especifico de download FTP paralelo.

---

## Estrutura de Modulos

```
src/
├── core/
│   ├── indicators.py         # Funcoes centralizadas para indicadores
│   ├── parallel.py           # ParallelFetcher
│   ├── collectors/
│   │   └── base.py           # BaseCollector
│   └── data/
│       ├── storage.py        # DataManager
│       └── query.py          # QueryEngine
├── bacen/
│   ├── sgs/
│   │   ├── client.py        # SGSClient
│   │   ├── collector.py     # SGSCollector
│   │   └── indicators.py    # SGS_CONFIG
│   └── expectations/
│       ├── client.py        # ExpectationsClient
│       ├── collector.py     # ExpectationsCollector
│       └── indicators.py    # EXPECTATIONS_CONFIG
├── mte/
│   └── caged/
│       ├── client.py        # CAGEDClient
│       ├── collector.py     # CAGEDCollector
│       └── indicators.py    # CAGED_CONFIG
├── ipea/
│   ├── client.py            # IPEAClient
│   ├── collector.py         # IPEACollector
│   └── indicators.py        # IPEA_CONFIG
└── bloomberg/
    ├── client.py            # BloombergClient
    ├── collector.py         # BloombergCollector
    └── indicators.py        # BLOOMBERG_CONFIG
```
