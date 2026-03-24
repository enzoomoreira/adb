# Camada de Servicos

Documentacao da camada `services/` - logica de aplicacao e coleta de dados.

---

## Visao Geral

A camada de servicos contem:

| Modulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **BaseCollector** | `collectors/base.py` | Classe base para coletores |
| **Registry** | `collectors/registry.py` | Mapeamento de collectors |

```
services/
├── __init__.py
└── collectors/
    ├── __init__.py
    ├── base.py       # BaseCollector
    └── registry.py   # Registro de collectors
```

---

## BaseCollector

**Localizacao:** `src/adb/services/collectors/base.py`

Classe base abstrata para todos os coletores de dados. Fornece infraestrutura comum para coleta incremental, logging e status.

### Responsabilidades

- Inicializacao padronizada com DataManager
- Logging padronizado (arquivo + console)
- Coleta incremental automatica via `_sync()`
- Status de arquivos salvos via `get_status()`

### Atributos de Classe

| Atributo | Tipo | Default | Descricao |
|----------|------|---------|-----------|
| `default_subdir` | `str` | `''` | Subdiretorio padrao para operacoes |

Subclasses **devem** sobrescrever este atributo:

```python
class SGSCollector(BaseCollector):
    default_subdir = 'bacen/sgs/daily'
```

### Inicializacao

```python
class BaseCollector:
    def __init__(self, data_path: Path = None):
        """
        Args:
            data_path: Caminho para data/ (opcional, usa get_settings().data_dir se None)
        """
```

**Componentes inicializados:**
- `data_manager`: DataManager com DisplayCallback
- `logger`: Logger loguru para arquivo
- `display`: Display singleton para console
- `_collect_total`: Acumulador de registros coletados

```python
from adb.services.collectors import BaseCollector

class MyCollector(BaseCollector):
    default_subdir = 'minha_fonte/daily'

    def __init__(self, data_path=None):
        super().__init__(data_path)
        # Inicializacoes especificas
        self.client = MyClient()
```

---

### Metodos Publicos

#### get_status()

Retorna DataFrame com status dos arquivos salvos.

```python
def get_status(self, subdir: str = None) -> pd.DataFrame
```

| Parametro | Descricao |
|-----------|-----------|
| `subdir` | Subdiretorio (default: `default_subdir`) |

**Colunas retornadas:**

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `arquivo` | `str` | Nome do indicador |
| `subdir` | `str` | Subdiretorio |
| `registros` | `int` | Numero de linhas |
| `primeira_data` | `date` | Data inicial |
| `ultima_data` | `date` | Data final |
| `cobertura` | `float` | Percentual 0-100 |
| `gaps` | `int` | Numero de lacunas |
| `status` | `str` | 'OK', 'STALE', 'GAPS', 'MISSING' |

```python
collector = SGSCollector()
status_df = collector.get_status()
print(status_df)
```

> **Importante:** Subclasses devem implementar `_get_frequency_for_file()` para que o DataValidator calcule corretamente as metricas.

---

### Metodos de Display

Metodos para output visual (console) e tecnico (arquivo):

#### _fetch_start()

Exibe inicio de fetch de indicador.

```python
def _fetch_start(self, name: str, start_date: str = None, verbose: bool = True)
```

```python
self._fetch_start("selic", "2024-01-01", verbose=True)
# Console: "[blue]selic[/blue] desde 2024-01-01..."
# Log: "Fetch start: selic, since=2024-01-01"
```

---

#### _fetch_result()

Exibe resultado de fetch.

```python
def _fetch_result(self, name: str, count: int, verbose: bool = True)
```

```python
self._fetch_result("selic", 275, verbose=True)
# Console: "275 registros"
# Log: "Fetch OK: selic, 275 registros"
```

> Acumula automaticamente em `_collect_total`.

---

#### _info(), _warning()

Mensagens informativas e avisos.

```python
self._info("Processando lote 1/5")
self._warning("Dados parciais retornados")
```

---

#### _start(), _end()

Banners de inicio e fim de coleta.

```python
def _start(
    self,
    title: str,
    num_indicators: int,
    subdir: str = None,
    check_first_run: bool = False,
    verbose: bool = True
)

def _end(self, verbose: bool = True)
```

```python
self._start("BACEN - SGS", num_indicators=5, check_first_run=True, verbose=True)
# Console: Banner com titulo e contagem

# ... coleta ...

self._end(verbose=True)
# Console: Banner de conclusao com total acumulado
```

---

### Metodos Auxiliares (Protegidos)

#### _normalize_indicators()

Normaliza entrada de indicadores para lista.

```python
def _normalize_indicators(
    self,
    indicators: list[str] | str,
    config: dict
) -> list[str]
```

| Entrada | Saida |
|---------|-------|
| `'all'` | `list(config.keys())` |
| `'selic'` | `['selic']` |
| `['selic', 'cdi']` | `['selic', 'cdi']` |

```python
keys = self._normalize_indicators('all', SGS_CONFIG)
# ['selic', 'cdi', 'ipca', ...]

keys = self._normalize_indicators('selic', SGS_CONFIG)
# ['selic']
```

---

#### _next_date()

Calcula proxima data esperada baseada na ultima data salva.

```python
def _next_date(
    self,
    last_date: pd.Timestamp | None,
    frequency: str
) -> str | None
```

| Frequencia | Logica |
|------------|--------|
| `'daily'` | Dia seguinte |
| `'monthly'` | Primeiro dia do proximo mes |
| `'quarterly'` | Primeiro dia do proximo trimestre |

```python
next_date = self._next_date(pd.Timestamp('2024-01-31'), 'monthly')
# '2024-02-01'

next_date = self._next_date(pd.Timestamp('2024-03-31'), 'quarterly')
# '2024-04-01'
```

---

#### _sync()

Template principal para coleta incremental. Orquestra todo o fluxo.

```python
def _sync(
    self,
    fetch_fn,
    filename: str,
    name: str,
    subdir: str,
    frequency: str = 'daily',
    save: bool = True,
    verbose: bool = True,
) -> None
```

| Parametro | Descricao |
|-----------|-----------|
| `fetch_fn` | Funcao que recebe `start_date` e retorna DataFrame |
| `filename` | Nome do arquivo (sem extensao) |
| `name` | Nome para exibicao |
| `subdir` | Subdiretorio dentro de data/ |
| `frequency` | 'daily', 'monthly' ou 'quarterly' |
| `save` | Se True, persiste resultados |
| `verbose` | Se True, exibe progresso |

**Fluxo interno:**

```mermaid
flowchart TD
    A[Inicio _sync] --> B[DataValidator.get_health]
    B --> C{Arquivo existe?}
    C -->|Nao| D[is_first_run = True]
    C -->|Sim| E[Calcular start_date]
    D --> F[Executar fetch_fn]
    E --> F
    F --> G{Dados retornados?}
    G -->|Nao| H[Log warning]
    G -->|Sim| I{is_first_run?}
    I -->|Sim| J[DataManager.save]
    I -->|Nao| K[DataManager.append]
    J --> L[_fetch_result]
    K --> L
    H --> L
```

```python
def collect(self, indicators='all', save=True, verbose=True):
    keys = self._normalize_indicators(indicators, MY_CONFIG)
    self._start("Minha Fonte", len(keys), verbose=verbose)

    for key in keys:
        cfg = MY_CONFIG[key]
        self._sync(
            fetch_fn=lambda start: self.client.fetch(cfg['code'], start),
            filename=key,
            name=cfg['name'],
            subdir=self.default_subdir,
            frequency=cfg.get('frequency', 'daily'),
            save=save,
            verbose=verbose
        )

    self._end(verbose=verbose)
```

---

#### _get_frequency_for_file()

Retorna frequencia de um indicador pelo nome do arquivo.

```python
def _get_frequency_for_file(self, filename: str) -> str | None
```

**Subclasses devem sobrescrever** para retornar a frequencia correta:

```python
class SGSCollector(BaseCollector):
    def _get_frequency_for_file(self, filename: str) -> str | None:
        if filename in SGS_CONFIG:
            return SGS_CONFIG[filename].get('frequency', 'daily')
        return None
```

---

### Template de Implementacao

Exemplo completo de como implementar um novo collector:

```python
from adb.services.collectors import BaseCollector
from adb.infra.resilience import retry

# 1. Configuracao de indicadores
MY_CONFIG = {
    'indicador1': {
        'name': 'Meu Indicador 1',
        'code': 123,
        'frequency': 'daily',
    },
    'indicador2': {
        'name': 'Meu Indicador 2',
        'code': 456,
        'frequency': 'monthly',
    },
}


# 2. Client para API externa
class MyClient:
    @retry(max_attempts=3, delay=1.0)
    def fetch(self, code: int, start_date: str = None) -> pd.DataFrame:
        """Busca dados da API com retry automatico."""
        params = {'codigo': code}
        if start_date:
            params['inicio'] = start_date

        response = httpx.get('https://api.exemplo.com/dados', params=params)
        response.raise_for_status()

        return pd.DataFrame(response.json())


# 3. Collector
class MyCollector(BaseCollector):
    default_subdir = 'minha_fonte/daily'

    def __init__(self, data_path=None):
        super().__init__(data_path)
        self.client = MyClient()

    def collect(
        self,
        indicators: list[str] | str = 'all',
        save: bool = True,
        verbose: bool = True,
    ):
        """Coleta dados da fonte."""
        keys = self._normalize_indicators(indicators, MY_CONFIG)

        self._start(
            title="Minha Fonte de Dados",
            num_indicators=len(keys),
            subdir=self.default_subdir,
            check_first_run=True,
            verbose=verbose
        )

        for key in keys:
            cfg = MY_CONFIG[key]
            freq = cfg.get('frequency', 'daily')

            # Determinar subdir por frequencia
            subdir = f'minha_fonte/{freq}'

            self._sync(
                fetch_fn=lambda start, c=cfg['code']: self.client.fetch(c, start),
                filename=key,
                name=cfg['name'],
                subdir=subdir,
                frequency=freq,
                save=save,
                verbose=verbose
            )

        self._end(verbose=verbose)

    def _get_frequency_for_file(self, filename: str) -> str | None:
        """Retorna frequencia do indicador para validacao."""
        if filename in MY_CONFIG:
            return MY_CONFIG[filename].get('frequency', 'daily')
        return None
```

---

## Registry

**Localizacao:** `src/adb/services/collectors/registry.py`

Registro interno de collectors para import dinamico.

### Mapeamento

```python
_COLLECTOR_MAP = {
    'sgs': ('bacen.sgs.collector', 'SGSCollector'),
    'expectations': ('bacen.expectations.collector', 'ExpectationsCollector'),
    'ipea': ('ipea.collector', 'IPEACollector'),
    'bloomberg': ('bloomberg.collector', 'BloombergCollector'),
    'sidra': ('ibge.sidra.collector', 'SidraCollector'),
}
```

### _get_collector()

Importa e retorna classe do collector (uso interno).

```python
def _get_collector(name: str):
    """
    Args:
        name: Nome do collector ('sgs', 'ipea', etc)

    Returns:
        Classe do collector

    Raises:
        ValueError: Se collector nao encontrado
    """
```

```python
from adb.services.collectors.registry import _get_collector

SGSCollector = _get_collector('sgs')
collector = SGSCollector()
collector.collect(['selic'])
```

### Adicionar Novo Collector

Para registrar um novo collector:

1. Crie o modulo em `providers/nova_fonte/`
2. Implemente `collector.py` com classe que herda de `BaseCollector`
3. Adicione entrada no `_COLLECTOR_MAP`:

```python
_COLLECTOR_MAP = {
    # ... existentes ...
    'nova_fonte': ('nova_fonte.collector', 'NovaFonteCollector'),
}
```

---

## Diagrama de Sequencia

Fluxo tipico de coleta:

```mermaid
sequenceDiagram
    participant User
    participant Explorer
    participant Collector
    participant Client
    participant DataManager
    participant DataValidator

    User->>Explorer: collect(['selic'])
    Explorer->>Collector: collect(indicators, save, verbose)

    Collector->>Collector: _normalize_indicators()
    Collector->>Collector: _start()

    loop Para cada indicador
        Collector->>DataValidator: get_health(filename, subdir, freq)
        DataValidator-->>Collector: HealthReport

        alt is_first_run
            Collector->>Client: fetch(code, None)
        else incremental
            Collector->>Client: fetch(code, start_date)
        end

        Client-->>Collector: DataFrame

        alt save=True
            alt is_first_run
                Collector->>DataManager: save(df, filename, subdir)
            else
                Collector->>DataManager: append(df, filename, subdir)
            end
        end

        Collector->>Collector: _fetch_result()
    end

    Collector->>Collector: _end()
    Collector-->>Explorer: None
    Explorer-->>User: None
```

---

## Imports Recomendados

```python
# Para criar novos collectors
from adb.services.collectors import BaseCollector

# Para acesso interno ao registry
from adb.services.collectors.registry import _get_collector
```

---

## Documentacao Relacionada

| Doc | Conteudo |
|-----|----------|
| [architecture.md](architecture.md) | Visao geral da arquitetura |
| [domain.md](domain.md) | BaseExplorer, Schemas, Exceptions |
| [infra.md](infra.md) | Config, Log, Resilience, Persistence |
