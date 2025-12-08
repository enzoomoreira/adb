# Utilitarios e Classes Base

Documentacao de componentes compartilhados do projeto.

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

Classe base para coletores do BCB.

**Localizacao:** `src/bacen/base.py`

### Visao Geral

Fornece funcionalidades comuns herdadas por `SGSCollector` e `ExpectationsCollector`:
- Delegacoes para DataManager
- Logging padronizado
- Metodo `get_status()` unificado

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
BaseCollector (src/bacen/base.py)
├── SGSCollector (src/bacen/sgs/collector.py)
└── ExpectationsCollector (src/bacen/expectations/collector.py)

CAGEDCollector (src/mte/caged/collector.py) - Independente, nao herda
IPEACollector (src/ipea/collector.py) - Independente, nao herda
```

**Por que CAGED e IPEA nao herdam?**
- Padrao de armazenamento diferente (arquivos mensais vs arquivo unico)
- API ligeiramente diferente (retorno int vs DataFrame)
- Independencia facilita evolucao separada

---

## Estrutura de Modulos

```
src/
├── core/
│   └── parallel.py          # ParallelFetcher
├── bacen/
│   ├── base.py              # BaseCollector
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
└── data/
    └── manager.py           # DataManager
```
