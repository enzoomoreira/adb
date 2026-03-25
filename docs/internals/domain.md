# Camada de Dominio

Documentacao da camada `domain/` - regras de negocio, entidades e validacao.

---

## Visao Geral

A camada de dominio contem:

| Modulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **BaseExplorer** | `explorers.py` | Interface unificada para leitura e coleta |
| **Exceptions** | `exceptions.py` | Hierarquia de excecoes customizadas |

```
domain/
├── __init__.py        # Exports publicos
├── exceptions.py      # ADBException, DataNotFoundError, etc.
└── explorers.py       # BaseExplorer
```

---

## BaseExplorer

**Localizacao:** `src/adb/domain/explorers.py`

Classe base abstrata que define a interface publica para leitura e coleta de dados. Todos os explorers especificos (SGSExplorer, IPEAExplorer, etc.) herdam desta classe.

### Atributos de Classe

Subclasses **devem** definir:

| Atributo | Tipo | Descricao |
|----------|------|-----------|
| `_CONFIG` | `dict` | Dicionario de configuracao de indicadores |
| `_SUBDIR` | `str` | Subdiretorio padrao para arquivos Parquet |
| `_COLLECTOR_CLASS` | `property` | Retorna classe do collector (lazy import) |

Subclasses **podem** sobrescrever:

| Atributo | Tipo | Default | Descricao |
|----------|------|---------|-----------|
| `_DATE_COLUMN` | `str` | `'date'` | Nome da coluna de data |

### Metodos Publicos

#### `__init__(self, query_engine=None)`

Inicializa o explorer.

```python
from adb.providers.bacen.sgs.explorer import SGSExplorer

# Usa QueryEngine padrao
explorer = SGSExplorer()

# Ou com QueryEngine customizado
from adb.infra.persistence import QueryEngine
qe = QueryEngine(base_path=Path('/custom/path'))
explorer = SGSExplorer(query_engine=qe)
```

---

#### `read(*indicators, start=None, end=None, columns=None) -> DataFrame`

Le series temporais do armazenamento.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `*indicators` | `str` | Nomes dos indicadores (vazio = todos) |
| `start` | `str` | Data inicial ('2020', '2020-01', '2020-01-15') |
| `end` | `str` | Data final |
| `columns` | `list[str]` | Colunas especificas (default: todas) |

**Retorno:** DataFrame com DatetimeIndex

**Comportamento:**
- Um indicador: retorna DataFrame direto com todas as colunas
- Multiplos indicadores: join por data, coluna `value` renomeada para nome do indicador

```python
import adb

# Um indicador - todas as colunas
df = adb.sgs.read('selic', start='2023')
# DataFrame com colunas: date (index), value

# Multiplos indicadores - join automatico
df = adb.sgs.read('selic', 'cdi', start='2023')
# DataFrame com colunas: date (index), selic, cdi
```

**Raises:** `KeyError` se indicador nao encontrado

---

#### `available(**filters) -> list[str]`

Lista indicadores disponiveis, opcionalmente filtrados.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `**filters` | kwargs | Filtros por atributo do config |

```python
import adb

# Todos os indicadores
adb.sgs.available()
# ['selic', 'cdi', 'dolar_ptax', 'ipca', ...]

# Filtrado por frequencia
adb.sgs.available(frequency='daily')
# ['selic', 'cdi', 'dolar_ptax']

adb.sgs.available(frequency='monthly')
# ['ipca', 'ibc_br_bruto', ...]
```

---

#### `info(indicator=None) -> dict`

Retorna informacoes sobre indicador(es).

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `indicator` | `str` | Nome do indicador (None = todos) |

```python
import adb

# Um indicador
adb.sgs.info('selic')
# {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily', ...}

# Todos
adb.sgs.info()
# {'selic': {...}, 'cdi': {...}, ...}
```

**Raises:** `KeyError` se indicador especifico nao encontrado

---

#### `collect(indicators='all', save=True, verbose=True, **kwargs)`

Coleta dados da fonte externa.

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `indicators` | `str \| list[str]` | `'all'` | Indicadores a coletar |
| `save` | `bool` | `True` | Se True, persiste em Parquet |
| `verbose` | `bool` | `True` | Se True, exibe progresso |
| `**kwargs` | kwargs | - | Argumentos extras para o collector |

```python
import adb

# Todos os indicadores
adb.sgs.collect()

# Indicador unico
adb.sgs.collect('selic')

# Lista de indicadores
adb.sgs.collect(['selic', 'cdi'])
```

---

#### `status() -> DataFrame`

Retorna status dos arquivos salvos.

```python
import adb

adb.sgs.status()
# DataFrame com colunas:
# - arquivo: nome do indicador
# - registros: numero de linhas
# - primeira_data, ultima_data
# - cobertura: percentual (0-100)
# - gaps: numero de lacunas
# - status: 'OK', 'STALE', 'GAPS', 'MISSING'
```

---

### Metodos Protegidos (Extension Points)

Para customizar comportamento em subclasses:

| Metodo | Descricao |
|--------|-----------|
| `_subdir(indicator)` | Retorna subdir dinamico por indicador |
| `_where(start, end)` | Constroi clausula WHERE para filtro |
| `_join(dfs, indicators)` | Logica de join de multiplos DataFrames |

```python
class SGSExplorer(BaseExplorer):
    def _subdir(self, indicator: str) -> str:
        """SGS usa subdir por frequencia."""
        freq = self._CONFIG[indicator].get('frequency', 'daily')
        return f'bacen/sgs/{freq}'
```

---

## Exceptions

**Localizacao:** `src/adb/domain/exceptions.py`

Hierarquia de excecoes customizadas para o pacote.

### Hierarquia

```mermaid
graph TD
    ADB["ADBException<br/><small>(base)</small>"]
    ADB --> DNF["DataNotFoundError<br/><small>Dados nao encontrados</small>"]
    ADB --> API["APIError<br/><small>Erros de API externa</small>"]
    API --> RL["RateLimitError<br/><small>Rate limit excedido</small>"]
    API --> CF["ConnectionFailedError<br/><small>Falha de conexao</small>"]

    style ADB fill:#f8d7da
    style DNF fill:#fff3cd
    style API fill:#fff3cd
    style RL fill:#d1ecf1
    style CF fill:#d1ecf1
```

### Classes

#### ADBException

Excecao base para o pacote. Todas as excecoes customizadas herdam desta.

```python
class ADBException(Exception):
    """Excecao base para o pacote adb."""
    pass
```

---

#### DataNotFoundError

Dados solicitados nao existem ou nao foram encontrados.

```python
from adb.domain.exceptions import DataNotFoundError

try:
    df = explorer.read('indicador_inexistente')
except DataNotFoundError as e:
    print(f"Dados nao encontrados: {e}")
```

---

#### APIError

Erro retornado por API externa.

```python
from adb.domain.exceptions import APIError

try:
    data = client.fetch(code=12345)
except APIError as e:
    print(f"Erro na API: {e}")
```

---

#### RateLimitError

Limite de requisicoes excedido pela API. Herda de `APIError`.

```python
from adb.domain.exceptions import RateLimitError

try:
    # Muitas requisicoes
    for i in range(1000):
        client.fetch(code=i)
except RateLimitError:
    print("Rate limit atingido, aguarde...")
```

---

#### ConnectionFailedError

Falha de conexao com servico externo. Herda de `APIError`.

```python
from adb.domain.exceptions import ConnectionFailedError

try:
    client.fetch(code=432)
except ConnectionFailedError:
    print("Falha de conexao - verifique sua rede")
```

---

## Uso Geral

### Imports Recomendados

```python
# API publica (para usuarios)
import adb
df = adb.sgs.read('selic')

# Imports diretos (para desenvolvedores)
from adb.domain import BaseExplorer, ADBException
from adb.domain.exceptions import DataNotFoundError, APIError
```

### Exemplo: Criar Novo Explorer

```python
from adb.domain import BaseExplorer

# 1. Definir configuracao (dicts simples, sem schemas)
MY_CONFIG = {
    'indicador1': {'name': 'Meu Indicador', 'code': 123, 'frequency': 'daily'},
}

# 2. Criar explorer
class MyExplorer(BaseExplorer):
    _CONFIG = MY_CONFIG
    _SUBDIR = 'minha_fonte/daily'

    @property
    def _COLLECTOR_CLASS(self):
        from minha_fonte.collector import MyCollector
        return MyCollector
```

---

## Documentacao Relacionada

| Doc | Conteudo |
|-----|----------|
| [architecture.md](architecture.md) | Visao geral da arquitetura |
| [infra.md](infra.md) | Config, Log, Resilience, Persistence |
| [services.md](services.md) | BaseCollector, Registry |
