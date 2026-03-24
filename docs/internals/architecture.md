# Arquitetura do Projeto

Documentacao tecnica da arquitetura Clean Architecture usada no `adb`.

---

## Visao Geral

O projeto segue **Clean Architecture** com cinco camadas principais, organizadas por responsabilidade:

| Camada | Diretorio | Responsabilidade |
|--------|-----------|------------------|
| **Domain** | `domain/` | Regras de negocio, entidades, excecoes, schemas Pydantic |
| **Infra** | `infra/` | I/O, configuracoes, logging, retry, persistencia |
| **Services** | `services/` | Logica de aplicacao, BaseCollector, registry |
| **Providers** | `providers/` | Implementacoes especificas por fonte de dados |
| **Shared** | `shared/` | Utilitarios compartilhados (datas, indicadores) |
| **UI** | `ui/` | Output visual ao usuario (Rich) |

### Principios

1. **Dependencias apontam para dentro**: Providers dependem de Services, Services dependem de Domain
2. **Domain e puro**: Sem dependencias externas (exceto Pydantic para validacao)
3. **Infra e o adaptador**: Conecta o sistema ao mundo externo (APIs, filesystem, logs)
4. **Inversao de dependencia**: Interfaces definidas em Domain, implementacoes em Infra

---

## Estrutura de Pastas

```
src/adb/
├── __init__.py              # Exports publicos (explorers, config)
│
├── domain/                  # CAMADA DE DOMINIO
│   ├── __init__.py          # Exports (BaseExplorer, exceptions, schemas)
│   ├── exceptions.py        # ADBException, DataNotFoundError, APIError, etc.
│   ├── explorers.py         # BaseExplorer (interface unificada de leitura)
│   └── schemas/             # Validacao Pydantic
│       ├── __init__.py
│       └── indicators.py    # IndicatorConfig, SGSIndicatorConfig, etc.
│
├── infra/                   # CAMADA DE INFRAESTRUTURA
│   ├── __init__.py          # Exports (get_settings, get_logger, retry)
│   ├── config.py            # Settings (platformdirs) e constantes de resiliencia
│   ├── log.py               # Sistema de logging (loguru)
│   ├── resilience.py        # Decorator @retry (tenacity)
│   └── persistence/         # Subcamada de persistencia
│       ├── __init__.py      # Exports (DataManager, QueryEngine)
│       ├── storage.py       # DataManager (I/O Parquet)
│       ├── query.py         # QueryEngine (DuckDB)
│       └── validation.py    # DataValidator (integridade)
│
├── services/                # CAMADA DE SERVICOS
│   ├── __init__.py
│   └── collectors/          # Abstracao de coleta
│       ├── __init__.py
│       ├── base.py          # BaseCollector
│       └── registry.py      # Mapeamento de collectors
│
├── providers/               # CAMADA DE PROVIDERS (por fonte)
│   ├── bacen/               # Banco Central
│   │   ├── sgs/             # client, collector, explorer, indicators
│   │   └── expectations/    # client, collector, explorer, indicators
│   ├── ibge/
│   │   └── sidra/           # client, collector, explorer, indicators
│   ├── ipea/                # client, collector, explorer, indicators
│   └── bloomberg/           # client, collector, explorer, indicators
│
├── shared/                  # UTILITARIOS COMPARTILHADOS
│   └── utils/
│       ├── dates.py         # parse_date, normalize_index
│       └── indicators.py    # list_keys, get_config
│
└── ui/                      # INTERFACE DE USUARIO
    ├── __init__.py
    └── display.py           # Output visual (Rich)
```

---

## Hierarquia de Classes

Diagrama mostrando heranca e composicao entre componentes:

```mermaid
classDiagram
    direction TB

    %% Domain Layer
    class BaseExplorer {
        <<abstract>>
        +_CONFIG: dict
        +_SUBDIR: str
        +_DATE_COLUMN: str
        +_COLLECTOR_CLASS: property
        +read(*indicators, start, end)
        +available(**filters)
        +info(indicator)
        +collect(indicators, save, verbose)
        +get_status()
        #_subdir(indicator)
        #_where(start, end)
        #_join(dfs, indicators)
    }

    class ADBException {
        <<exception>>
    }
    class DataNotFoundError
    class APIError
    class RateLimitError
    class ConnectionFailedError

    class IndicatorConfig {
        <<pydantic>>
        +name: str
        +frequency: FrequencyType
        +description: str?
    }
    class SGSIndicatorConfig {
        +code: int
    }
    class IPEAIndicatorConfig {
        +code: str
        +unit: str?
        +source: str?
    }
    class SIDRAIndicatorConfig {
        +code: int
        +parameters: dict
    }

    %% Services Layer
    class BaseCollector {
        <<abstract>>
        +default_subdir: str
        +data_manager: DataManager
        +display: Display
        +get_status(subdir)
        #_normalize_indicators(indicators, config)
        #_next_date(last_date, frequency)
        #_sync(fetch_fn, filename, ...)
        #_start(title, num_indicators, ...)
        #_end(verbose)
        #_fetch_start(name, start_date)
        #_fetch_result(name, count)
        #_get_frequency_for_file(filename)
    }

    %% Infra Layer
    class DataManager {
        +base_path: Path
        +save(df, filename, subdir, ...)
        +read(filename, subdir)
        +append(df, filename, subdir, ...)
        +get_metadata(filename, subdir)
        +get_last_date(filename, subdir)
        +list_files(subdir)
        +is_first_run(subdir)
        +get_file_path(filename, subdir)
    }

    class QueryEngine {
        +base_path: Path
        +read(filename, subdir, columns, where)
        +read_glob(pattern, subdir, ...)
        +sql(query, subdir)
        +aggregate(filename, subdir, group_by, agg)
        +get_metadata(filename, subdir)
        +connection()
    }

    class DataValidator {
        +STALE_THRESHOLD: dict
        +COVERAGE_THRESHOLD: float
        +get_health(filename, subdir, frequency)
    }

    %% Providers (exemplos)
    class SGSExplorer
    class SGSCollector
    class ExpectationsExplorer
    class ExpectationsCollector

    %% Relationships - Domain
    ADBException <|-- DataNotFoundError
    ADBException <|-- APIError
    APIError <|-- RateLimitError
    APIError <|-- ConnectionFailedError

    IndicatorConfig <|-- SGSIndicatorConfig
    IndicatorConfig <|-- IPEAIndicatorConfig
    IndicatorConfig <|-- SIDRAIndicatorConfig

    %% Relationships - Services/Providers
    BaseExplorer <|-- SGSExplorer
    BaseExplorer <|-- ExpectationsExplorer

    BaseCollector <|-- SGSCollector
    BaseCollector <|-- ExpectationsCollector

    %% Composition
    BaseExplorer o-- QueryEngine : usa
    BaseCollector o-- DataManager : usa
    BaseCollector o-- DataValidator : usa
    DataManager o-- QueryEngine : delega leituras
```

---

## Fluxo de Dados

Diagrama do fluxo completo desde coleta ate visualizacao:

```mermaid
flowchart TD
    User["Usuario<br/>(Notebook/Script)"]

    subgraph Coleta ["1. COLETA"]
        direction TB
        EC["Explorer.collect()"]
        CC["Collector.collect()"]
        CLI["Client<br/>(API externa)"]
        RET["@retry<br/>(tenacity)"]
        RAW["Dados brutos"]
        DM["DataManager.save/append()"]
    end

    subgraph Leitura ["2. LEITURA"]
        direction TB
        ER["Explorer.read()"]
        QE["QueryEngine<br/>(DuckDB SQL)"]
    end

    subgraph Saida ["3. SAIDA"]
        direction TB
        DF["DataFrame"]
    end

    PARQUET[("data/*.parquet")]

    %% Fluxo de Coleta
    User --> EC
    EC -->|"instancia"| CC
    CC -->|"chama"| CLI
    CLI -.->|"decorado"| RET
    CLI --> RAW
    RAW --> DM
    DM -->|"persiste"| PARQUET

    %% Fluxo de Leitura
    User --> ER
    PARQUET -->|"le"| ER
    ER -->|"delega"| QE
    QE --> DF

    %% Styling
    style Coleta fill:#e8f4e8
    style Leitura fill:#e8e8f4
    style Saida fill:#f4e8e8
```

### Detalhes do Fluxo

#### 1. Coleta

```python
import adb

# Usuario chama collect no Explorer
adb.sgs.collect(['selic', 'cdi'])

# Internamente:
# 1. Explorer instancia Collector
# 2. Collector usa _sync() para orquestrar
# 3. Client faz requisicao (com @retry)
# 4. DataManager salva em Parquet
```

#### 2. Leitura

```python
# Usuario chama read no Explorer
df = adb.sgs.read('selic', start='2023')

# Internamente:
# 1. Explorer constroi WHERE clause
# 2. QueryEngine executa SQL no DuckDB
# 3. Retorna DataFrame com DatetimeIndex
```

---

## Padroes de Projeto

| Padrao | Onde | Descricao |
|--------|------|-----------|
| **Template Method** | `BaseCollector._sync()` | Define esqueleto do algoritmo; subclasses implementam `fetch_fn` |
| **Facade** | `BaseExplorer` | Simplifica acesso a Collector + QueryEngine |
| **Strategy** | `StorageCallback` | Callback protocol para feedback de storage |
| **Lazy Loading** | `__init__.py` | Explorers carregados sob demanda |
| **Decorator** | `@retry` | Resiliencia de rede via tenacity |
| **Singleton** | `get_display()` | Instancia unica de Display (thread-safe) |
| **Composition** | `DataManager -> QueryEngine` | DataManager delega leituras para QueryEngine |

---

## Dependencias entre Camadas

```mermaid
graph TD
    subgraph External ["Externo"]
        APIs["APIs<br/>(BCB, IBGE, etc)"]
        FS["Filesystem"]
    end

    subgraph App ["Aplicacao"]
        UI["ui/"]
        PROV["providers/"]
        SERV["services/"]
        INFRA["infra/"]
        DOM["domain/"]
        SHARED["shared/"]
    end

    %% Dependencias permitidas
    PROV --> SERV
    PROV --> DOM
    PROV --> INFRA
    SERV --> DOM
    SERV --> INFRA
    INFRA --> DOM
    UI --> INFRA

    %% Shared e transversal
    PROV -.-> SHARED
    SERV -.-> SHARED
    INFRA -.-> SHARED

    %% Conexoes externas (apenas Infra)
    INFRA --> APIs
    INFRA --> FS

    style DOM fill:#d4edda
    style INFRA fill:#cce5ff
    style SERV fill:#fff3cd
    style PROV fill:#f8d7da
    style SHARED fill:#e2e3e5
    style UI fill:#d1ecf1
```

**Regra de Ouro**: Domain nunca depende de outras camadas internas.

---

## Documentacao Relacionada

| Doc | Conteudo |
|-----|----------|
| [domain.md](domain.md) | BaseExplorer, Schemas, Exceptions |
| [infra.md](infra.md) | Config, Log, Resilience, Persistence |
| [services.md](services.md) | BaseCollector, Registry |
