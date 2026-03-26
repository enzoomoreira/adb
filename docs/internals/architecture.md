# Arquitetura

Documentacao tecnica da estrutura interna do adb.

---

## Estrutura de Pastas

```
src/adb/
    __init__.py              # Registry de explorers (importlib + dict)
    explorer.py              # BaseExplorer (interface publica unificada)
    collector.py             # BaseCollector (generico, parametrizado)
    display.py               # Display singleton (Rich)
    utils.py                 # parse_date, normalize_index, DATE_COLUMNS
    exceptions.py            # ADBException, APIError, DataNotFoundError
    infra/
        config.py            # Settings (platformdirs), constantes de resilience
        log.py               # Logging (loguru, lazy init, file rotation)
        resilience.py        # @retry (tenacity, exponential backoff)
        query.py             # QueryEngine (DuckDB sobre Parquet)
        storage.py           # DataManager (save/append Parquet, dedup)
        validation.py        # DataValidator (health checks, gaps, cobertura)
    providers/
        bacen/
            sgs/             # client.py, explorer.py, indicators.py
            expectations/    # client.py, explorer.py, indicators.py
        ibge/
            sidra/           # client.py, explorer.py, indicators.py
        ipea/                # client.py, explorer.py, indicators.py
        bloomberg/           # client.py, explorer.py, indicators.py
```

Cada provider tem 3 arquivos:
- `indicators.py` -- dict `_CONFIG` com catalogo curado
- `client.py` -- wrapper stateless da API com `get_data(config, start, end) -> DataFrame`
- `explorer.py` -- herda `BaseExplorer`, declara config/client/subdir/title

Nao existem collectors concretos. O `BaseCollector` e generico e parametrizado.

---

## Fluxo de Dados

### fetch() -- stateless, sem disco

```
adb.sgs.fetch("selic", start="2020")
    |
    v
BaseExplorer.fetch()
    -> _fetch_one(indicator, start, end)
        -> _CLIENT_CLASS().get_data(config, start, end)
            -> API externa (python-bcb, ipeadatapy, etc.)
    -> normalize_index(df)
    -> rename "value" -> indicator name
    -> return DataFrame
```

### collect() + read() -- com cache local

```
adb.sgs.collect()
    |
    v
BaseExplorer.collect()
    -> BaseCollector(config, title, client_class, subdir_template)
        -> collect() template method:
            1. _normalize_indicators()
            2. _start() (banner)
            3. for key in indicators:
                _collect_one(key, config, start, end, save, verbose)
                    -> client.get_data(config, start, end)
                    -> _persist(fetch_fn, filename, subdir, frequency)
                        -> get_last_date() (incremental)
                        -> DataManager.save() ou .append()
            4. _end() (banner)

adb.sgs.read("selic", start="2020")
    |
    v
BaseExplorer.read()
    -> QueryEngine.read(filename, subdir, where="date >= '2020-01-01'")
    -> normalize_index(df)
    -> rename "value" -> indicator name
    -> return DataFrame
```

---

## Componentes Principais

### BaseExplorer (`explorer.py`)

Interface publica. Todos os explorers herdam desta classe.

**Atributos de classe** (subclass define):
- `_CONFIG: dict` -- catalogo de indicadores
- `_SUBDIR_TEMPLATE: str` -- template de subdir (ex: `"bacen/sgs/{frequency}"`)
- `_CLIENT_CLASS: type` -- classe do client
- `_TITLE: str` -- titulo para banners de coleta

**Metodos publicos**:
- `read(*indicators, start, end, columns)` -- le do cache Parquet
- `fetch(*indicators, start, end)` -- busca direto da API (stateless)
- `collect(indicators, start, end, save, verbose)` -- coleta e persiste
- `available(**filters)` -- lista indicadores, filtro opcional
- `info(indicator)` -- retorna config do indicador
- `status()` -- health check dos dados salvos

**Extension points**:
- `_fetch_one()` -- generico na base, override para casos especiais (Expectations)
- `_subdir()` -- resolve template com frequency do config
- `_join()` -- outer join por data (override: Expectations faz concat)

### BaseCollector (`collector.py`)

Classe concreta parametrizada. O Explorer cria instancias no construtor.

```python
collector = BaseCollector(
    config=self._CONFIG,
    title=self._TITLE,
    client_class=self._CLIENT_CLASS,
    subdir_template=self._SUBDIR_TEMPLATE,
)
```

**Responsabilidades**:
- Template method `collect()` (loop sequencial por indicadores)
- `_collect_one()` generico: chama `client.get_data(config, start, end)`
- `_persist()` com incrementalidade (get_last_date + _next_date)
- `status()` com health checks via DataValidator
- Display (banners, fetch_start/fetch_result) via Display singleton

### Client Protocol

Todos os clients seguem a mesma interface:

```python
class SomeClient:
    def get_data(self, config: dict, start_date: str | None, end_date: str | None) -> pd.DataFrame:
        # Extrai do config o que precisa (code, ticker, endpoint, etc.)
        # Chama API externa
        # Normaliza para DatetimeIndex + coluna "value"
        ...
```

O client recebe o dict de config completo e extrai internamente os campos
que precisa. Nao existe interface formal (Protocol) -- duck typing.

### Infra

| Modulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| Config | `infra/config.py` | Settings via platformdirs, constantes de retry |
| Log | `infra/log.py` | Logging loguru com lazy init e file rotation |
| Resilience | `infra/resilience.py` | `@retry` com tenacity, exponential backoff |
| Query | `infra/query.py` | QueryEngine (DuckDB SQL sobre Parquet) |
| Storage | `infra/storage.py` | DataManager (save/append com dedup atomico) |
| Validation | `infra/validation.py` | DataValidator (health checks, gaps, cobertura) |

---

## Excecoes

```
ADBException (base)
+-- DataNotFoundError
+-- APIError
```

`@retry` absorve erros transientes de rede. Excecoes especificas
(`RateLimitError`, `ConnectionFailedError`) foram removidas por nao
serem usadas.

---

## Padroes de Projeto

| Padrao | Onde | Descricao |
|--------|------|-----------|
| **Facade** | `BaseExplorer` | Simplifica acesso a Client + Collector + QueryEngine |
| **Parametrized Factory** | `BaseCollector` | Recebe config no construtor, sem subclasses |
| **Registry** | `__init__.py` | Dict + importlib para lazy loading de explorers |
| **Strategy** | `StorageCallback` | Protocol para feedback visual no DataManager |
| **Decorator** | `@retry` | Resilience de rede via tenacity |
| **Singleton** | `get_display()` | Instancia unica de Display (thread-safe) |
| **Composition** | `DataManager -> QueryEngine` | DataManager delega leituras |
