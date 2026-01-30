# Modulo Core (adb.core)

Documentacao do modulo central do projeto agora-database.

---

## Visao Geral

O modulo `adb.core` fornece a infraestrutura compartilhada por todos os coletores e exploradores de dados. Inclui:

- **Configuracao** - Paths e constantes globais
- **Logging** - Logs tecnicos em arquivo com rotacao
- **Display** - Output visual ao usuario (banners, progresso, cores ANSI)
- **Resiliencia** - Retry com backoff exponencial para APIs
- **Excecoes** - Hierarquia de erros customizados
- **Collectors** - Classe base para coleta de dados
- **Data** - Persistencia (DataManager), queries (QueryEngine), exploradores (BaseExplorer) e validacao (DataValidator)
- **Utils** - Funcoes auxiliares de datas e indicadores

> **Nota:** O sistema de visualizacao foi movido para a biblioteca externa **chartkit**.

### Estrutura de Arquivos

```
src/adb/core/
├── __init__.py           # API publica centralizada
├── config.py             # Configuracao global (paths, timeouts)
├── log.py                # Logging tecnico (apenas arquivo)
├── display.py            # Output visual ao usuario (console)
├── resilience.py         # Decorator @retry
├── exceptions.py         # Excecoes customizadas
├── collectors/
│   ├── base.py           # BaseCollector
│   └── registry.py       # Registro de collectors
├── data/
│   ├── storage.py        # DataManager (I/O Parquet)
│   ├── query.py          # QueryEngine (DuckDB)
│   ├── explorers.py      # BaseExplorer
│   └── validation.py     # DataValidator (validacao de integridade)
└── utils/
    ├── dates.py          # parse_date, normalize_index
    └── indicators.py     # list_keys, get_config
```

---

## Imports Principais

```python
# API publica (recomendado)
import adb
adb.sgs.read('selic')
adb.caged.read(year=2024)

# Classes para uso avancado
from adb import QueryEngine, DataManager

# Configuracao de paths
from adb import PROJECT_ROOT, DATA_PATH, OUTPUTS_PATH
```

---

## core.config

**Localizacao:** `src/adb/core/config.py`

Configuracao global do projeto com deteccao automatica do diretorio raiz.

### Constantes de Path

| Constante | Descricao |
|-----------|-----------|
| `PROJECT_ROOT` | Raiz do projeto (detecta `pyproject.toml` ou `.git`) |
| `DATA_PATH` | Diretorio de dados (`{PROJECT_ROOT}/data`) |
| `OUTPUTS_PATH` | Diretorio de saidas (`{PROJECT_ROOT}/data/outputs`) |
| `LOG_PATH` | Diretorio de logs (`{PROJECT_ROOT}/logs`) |

### Constantes de Resiliencia

| Constante | Valor | Descricao |
|-----------|-------|-----------|
| `DEFAULT_REQUEST_TIMEOUT` | 30 | Timeout HTTP em segundos |
| `DEFAULT_RETRY_ATTEMPTS` | 3 | Tentativas maximas |
| `DEFAULT_RETRY_DELAY` | 1.0 | Delay inicial em segundos |
| `DEFAULT_BACKOFF_FACTOR` | 2.0 | Multiplicador de backoff |
| `DEFAULT_CHUNK_DELAY` | 2.0 | Delay entre chunks de requisicoes |

```python
from adb.core import PROJECT_ROOT, DATA_PATH

print(PROJECT_ROOT)  # Path do diretorio raiz
print(DATA_PATH)     # Path do diretorio de dados
```

---

## core.log

**Localizacao:** `src/adb/core/log.py`

Sistema de logging tecnico centralizado. Registra informacoes detalhadas apenas em arquivo para debugging e auditoria.

### get_logger(name)

Cria ou retorna logger configurado.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| name | str | Nome do logger (geralmente `__name__`) |

**Retorno:** `logging.Logger`

**Caracteristicas:**
- **Arquivo:** DEBUG+, rotacao 10MB, 5 backups em `logs/adb_YYYY-MM-DD.log`
- **Formato:** `[YYYY-MM-DD HH:MM:SS] LEVEL [logger_name] message`
- **Sem console:** Output visual ao usuario e feito via `Display` (ver `core.display`)

```python
from adb.core.log import get_logger

logger = get_logger(__name__)
logger.info("Registro tecnico para arquivo")
logger.debug("Detalhes de debugging")
```

---

## core.display

**Localizacao:** `src/adb/core/display.py`

Sistema de output visual para o usuario. Separa feedback visual (console) de logging tecnico (arquivo).

### Display

Classe que gerencia output visual. Responsabilidades:
- Banners e separadores
- Mensagens de progresso e status
- Barras de progresso (via tqdm)
- Formatacao consistente
- Cores ANSI para destaque (warning/error/banners)

**Thread-safety:**
- Usa `tqdm.write()` quando ha barras ativas (evita output corrompido)
- Contador de barras protegido por lock

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| verbose | bool | True | Se True, exibe mensagens. Se False, silencia tudo |
| stream | TextIO | sys.stdout | Stream de saida |
| colors | bool | True | Usa cores ANSI quando suportado |

#### Metodos

| Metodo | Descricao |
|--------|-----------|
| `banner(title, subtitle, first_run, indicator_count)` | Banner de inicio de coleta |
| `end_banner(total)` | Banner de conclusao |
| `separator()` | Linha separadora |
| `fetch_start(name, since)` | Inicio de fetch de indicador |
| `fetch_result(count)` | Resultado de fetch |
| `saved(path)` | Arquivo salvo |
| `appended(path)` | Arquivo atualizado (append) |
| `warning(message)` | Aviso (amarelo) |
| `error(message)` | Erro (vermelho) |
| `info(message)` | Mensagem informativa |
| `progress(iterable, total, desc, unit, leave)` | Barra de progresso |

### get_display(verbose=True)

Retorna instancia unica de Display (Singleton thread-safe).

Usa double-checked locking para performance:
- Primeiro check sem lock (rapido, 99% dos casos)
- Segundo check com lock (apenas na criacao)

```python
from adb.core.display import get_display

display = get_display(verbose=True)
display.banner("BACEN - SGS", indicator_count=10, first_run=True)
display.fetch_start("selic", "2024-01-01")
display.fetch_result(275)
display.end_banner(total=275)

# Com barra de progresso
for item in display.progress(items, total=100, desc="Processando"):
    process(item)
```

---

## core.resilience

**Localizacao:** `src/adb/core/resilience.py`

Decorator para retry automatico com backoff exponencial.

### @retry()

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| max_attempts | int | 3 | Numero maximo de tentativas |
| delay | float | 1.0 | Delay inicial em segundos |
| backoff_factor | float | 2.0 | Multiplicador do delay |
| exceptions | tuple | TRANSIENT_EXCEPTIONS | Excecoes que disparam retry |
| jitter | bool | True | Adiciona variacao aleatoria (0.5x-1.5x) |

**Excecoes Transientes (retry automatico):**
- `requests.RequestException`, `ConnectionError`, `Timeout`
- `urllib3.exceptions.HTTPError`
- `OSError`, `TimeoutError`
- `json.JSONDecodeError`, `ValueError`

```python
from adb.core.resilience import retry

@retry(max_attempts=3, delay=1.0)
def fetch_data(url):
    return requests.get(url, timeout=30)
```

---

## core.exceptions

**Localizacao:** `src/adb/core/exceptions.py`

Hierarquia de excecoes customizadas.

```mermaid
graph TD
    ADB["ADBException<br/>(base)"]
    ADB --> DNF["DataNotFoundError<br/><small>Dados nao encontrados</small>"]
    ADB --> API["APIError<br/><small>Erros de API externa</small>"]
    API --> RL["RateLimitError<br/><small>Rate limit excedido</small>"]
    API --> CF["ConnectionFailedError<br/><small>Falha de conexao</small>"]
```

```python
from adb.core.exceptions import DataNotFoundError, APIError

try:
    df = explorer.read('indicador_inexistente')
except DataNotFoundError as e:
    print(f"Dados nao encontrados: {e}")
```

---

## core.collectors

**Localizacao:** `src/adb/core/collectors/`

Sistema de coleta de dados com classe base e registro de collectors.

### BaseCollector

Classe base para todos os coletores. Fornece:
- Logging padronizado
- Coleta incremental automatica
- Gerenciamento de status

#### Atributos de Classe

| Atributo | Tipo | Descricao |
|----------|------|-----------|
| `default_subdir` | str | Subdiretorio padrao para arquivos |

#### Metodos Publicos

##### get_status(subdir=None)

Retorna DataFrame com status dos arquivos salvos. Usa `DataValidator` para calcular metricas de saude dos dados.

| Coluna | Descricao |
|--------|-----------|
| arquivo | Nome do arquivo |
| subdir | Subdiretorio |
| registros | Numero de linhas |
| colunas | Numero de colunas |
| primeira_data | Data inicial |
| ultima_data | Data final |
| cobertura | Percentual de cobertura (0-100) |
| gaps | Numero de lacunas nos dados |
| status | 'OK', 'STALE', 'GAPS' ou 'MISSING' |

> **Nota:** Subclasses devem implementar `_get_frequency_for_file(filename, subdir)` para que o DataValidator calcule corretamente as metricas baseado na frequencia do indicador.

#### Metodos Auxiliares (Protegidos)

| Metodo | Descricao |
|--------|-----------|
| `_normalize_indicators(indicators, config)` | Normaliza entrada para lista |
| `_next_date(last_date, frequency)` | Calcula data inicial para coleta incremental (suporta 'daily', 'monthly', 'quarterly') |
| `_sync(fetch_fn, filename, ...)` | Template para coleta com sync automatico (usa health check antes de coletar) |
| `_start(title, num_indicators, ...)` | Banner de inicio |
| `_end(results, verbose)` | Banner de fim |
| `_fetch_start(name, start_date, verbose)` | Log de inicio de fetch |
| `_fetch_result(name, count, verbose)` | Log de resultado |
| `_get_frequency_for_file(filename, subdir)` | Retorna frequencia do indicador (subclasses devem implementar) |

#### Exemplo de Implementacao

```python
from adb.core.collectors import BaseCollector

class NovoCollector(BaseCollector):
    default_subdir = 'nova_fonte/daily'

    def __init__(self, data_path=None):
        super().__init__(data_path)
        self.client = NovoClient()

    def collect(self, indicators='all', save=True, verbose=True):
        keys = self._normalize_indicators(indicators, NOVA_CONFIG)
        self._start("Nova Fonte", len(keys), verbose=verbose)

        for key in keys:
            cfg = NOVA_CONFIG[key]
            self._sync(
                fetch_fn=lambda start: self.client.fetch(cfg['code'], start),
                filename=key,
                name=cfg['name'],
                subdir=self.default_subdir,
                frequency=cfg.get('frequency', 'daily'),
                save=save,
                verbose=verbose
            )
```

### Registro de Collectors

O arquivo `registry.py` mapeia nomes para classes de collectors:

| Nome | Classe | Modulo |
|------|--------|--------|
| sgs | SGSCollector | bacen.sgs |
| expectations | ExpectationsCollector | bacen.expectations |
| caged | CAGEDCollector | mte.caged |
| ipea | IPEACollector | ipea |
| bloomberg | BloombergCollector | bloomberg |
| sidra | SidraCollector | ibge.sidra |

---

## core.data

**Localizacao:** `src/adb/core/data/`

Camada de persistencia e acesso a dados.

### DataManager

Gerencia I/O de arquivos Parquet com compressao Snappy.

#### Metodos

| Metodo | Assinatura | Descricao |
|--------|------------|-----------|
| `save` | `(df, filename, subdir='daily', format='parquet', metadata=None, verbose=False)` | Salva DataFrame |
| `read` | `(filename, subdir='daily') -> DataFrame` | Le arquivo |
| `append` | `(df, filename, subdir='daily', dedup=True, verbose=False)` | Append incremental |
| `get_metadata` | `(filename, subdir='daily') -> dict` | Metadados do arquivo |
| `get_last_date` | `(filename, subdir='daily') -> datetime` | Ultima data salva |
| `list_files` | `(subdir='daily') -> list[str]` | Lista arquivos |
| `is_first_run` | `(subdir) -> bool` | Verifica primeira execucao |
| `get_file_path` | `(filename, subdir) -> Path` | Path completo |

```python
from adb.core import DataManager

dm = DataManager()

# Salvar
dm.save(df, 'selic', subdir='bacen/sgs/daily')

# Ler
df = dm.read('selic', subdir='bacen/sgs/daily')

# Append incremental (deduplica por data)
dm.append(new_data, 'selic', subdir='bacen/sgs/daily')

# Verificar ultima data
last = dm.get_last_date('selic', subdir='bacen/sgs/daily')
```

### QueryEngine

Motor de queries SQL sobre Parquet usando DuckDB.

#### Metodos

| Metodo | Assinatura | Descricao |
|--------|------------|-----------|
| `read` | `(filename, subdir='daily', columns=None, where=None) -> DataFrame` | Le com filtros |
| `read_glob` | `(pattern, subdir=None, columns=None, where=None) -> DataFrame` | Le multiplos arquivos |
| `sql` | `(query, subdir=None) -> DataFrame` | SQL arbitrario |
| `aggregate` | `(filename, subdir, group_by, agg, where=None) -> DataFrame` | Agregacao |
| `get_metadata` | `(filename, subdir) -> dict` | Metadados otimizados |
| `connection` | `() -> DuckDBPyConnection` | Conexao configurada |

```python
from adb.core import QueryEngine

qe = QueryEngine()

# Leitura com filtro
df = qe.read('selic', subdir='bacen/sgs/daily',
             where="date >= '2023-01-01'")

# Leitura de multiplos arquivos
df = qe.read_glob('cagedmov_2024-*.parquet',
                  subdir='mte/caged',
                  columns=['competencia', 'saldo'])

# SQL direto (variaveis: {raw}, {processed}, {subdir})
df = qe.sql("""
    SELECT date, value
    FROM '{raw}/bacen/sgs/daily/selic.parquet'
    WHERE date >= '2020-01-01'
""")

# Agregacao
df = qe.aggregate('selic', 'bacen/sgs/daily',
                  group_by='YEAR(date)',
                  agg={'value': 'AVG'})
```

### BaseExplorer

Classe base para exploradores de dados. Interface unificada para leitura e coleta.

#### Atributos de Classe (Subclasses devem definir)

| Atributo | Tipo | Descricao |
|----------|------|-----------|
| `_CONFIG` | dict | Configuracao de indicadores |
| `_SUBDIR` | str | Subdiretorio padrao |
| `_DATE_COLUMN` | str | Nome da coluna de data (default: 'date') |
| `_COLLECTOR_CLASS` | property | Classe do collector |

#### Metodos Publicos

##### read(*indicators, start=None, end=None, columns=None)

Le series temporais.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| *indicators | str | Indicadores a ler (vazio = todos) |
| start | str | Data inicial ('2020', '2020-01', '2020-01-15') |
| end | str | Data final |
| columns | list | Colunas especificas |

**Retorno:** DataFrame com DatetimeIndex

```python
from adb.core.data import sgs

# Um indicador
df = sgs.read('selic', start='2023')

# Multiplos indicadores (join por data)
df = sgs.read('selic', 'cdi', start='2023')
```

##### available(**filters)

Lista indicadores disponiveis.

```python
sgs.available()
# ['selic', 'cdi', 'dolar_ptax', ...]

sgs.available(frequency='monthly')
# ['ibc_br_bruto', 'ipca', ...]
```

##### info(indicator=None)

Retorna configuracao do indicador.

```python
sgs.info('selic')
# {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily'}
```

##### collect(indicators='all', save=True, verbose=True, **kwargs)

Coleta dados da fonte.

```python
sgs.collect('selic')           # Um indicador
sgs.collect(['selic', 'cdi'])  # Lista
sgs.collect()                  # Todos
```

##### get_status()

Retorna status dos arquivos salvos.

```python
sgs.get_status()
# DataFrame com: arquivo, registros, primeira_data, ultima_data, status
```

### Exploradores Disponiveis

Acessiveis via `adb.core.data` (lazy-loaded):

| Explorer | Fonte | Dados |
|----------|-------|-------|
| `sgs` | BCB/SGS | Series temporais (Selic, CDI, IPCA, cambio) |
| `expectations` | BCB/Focus | Expectativas de mercado |
| `caged` | MTE | Microdados de emprego formal |
| `ipea` | IPEA | Dados agregados de emprego |
| `bloomberg` | Bloomberg | Dados de mercado (Terminal) |
| `sidra` | IBGE/SIDRA | Dados demograficos e economicos |

---

## core.data.validation

**Localizacao:** `src/adb/core/data/validation.py`

Sistema de validacao de integridade de dados. Usa **cuallee** para checks de qualidade e **bizdays** (calendario ANBIMA) para calcular dias uteis brasileiros.

### HealthStatus

Enum que representa o status de saude dos dados:

| Status | Descricao |
|--------|-----------|
| `OK` | Dados completos e atualizados |
| `STALE` | Dados desatualizados (ultima data muito antiga) |
| `GAPS` | Dados com lacunas (cobertura < 95%) |
| `MISSING` | Arquivo nao existe |

### HealthReport

Dataclass com metricas de saude:

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `status` | HealthStatus | Status de saude |
| `first_date` | date | Data inicial |
| `last_date` | date | Data final |
| `expected_records` | int | Registros esperados |
| `actual_records` | int | Registros reais |
| `coverage` | float | Cobertura percentual (0-100) |
| `gaps` | list[Gap] | Lacunas nos dados |
| `stale_days` | int | Dias desde ultima atualizacao |
| `cuallee_results` | dict | Resultados dos checks cuallee (is_complete, is_unique) |

### DataValidator

Validador de integridade com context manager.

#### Uso

```python
from adb.core.data.validation import DataValidator, HealthStatus

with DataValidator() as validator:
    health = validator.get_health('selic', 'bacen/sgs/daily', 'daily')
    print(health.status)     # HealthStatus.OK
    print(health.coverage)   # 98.5
    print(health.stale_days) # 2
```

#### get_health(filename, subdir, frequency)

Analisa saude dos dados de um arquivo.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| filename | str | Nome do arquivo (sem .parquet) |
| subdir | str | Subdiretorio dentro de raw/ |
| frequency | str | 'daily', 'monthly' ou 'quarterly' |

**Retorno:** `HealthReport`

**Comportamento:**
- Para `daily`: usa calendario ANBIMA para dias uteis brasileiros
- Para `monthly`: espera primeiro dia de cada mes
- Para `quarterly`: espera primeiro dia de cada trimestre (jan, abr, jul, out)
- Executa checks cuallee: `is_complete` (sem nulos) e `is_unique` (sem duplicatas) na coluna date

**Limiares de Staleness:**
- Daily: 3 dias uteis
- Monthly: 45 dias
- Quarterly: 95 dias

---

## core.utils

**Localizacao:** `src/adb/core/utils/`

Funcoes auxiliares compartilhadas.

### Funcoes de Indicadores

**Localizacao:** `src/adb/core/utils/indicators.py`

> **Nota:** Funcoes de uso interno. Para o usuario final, usar os metodos do explorer:

```python
import adb

# Listar indicadores
adb.sgs.available()                        # ['selic', 'cdi', ...]
adb.sgs.available(frequency='daily')       # Filtrado

# Obter config de um indicador
adb.sgs.info('selic')                      # {'code': 432, 'name': ...}

# Listar todos com detalhes
adb.sgs.info()                             # {'selic': {...}, 'cdi': {...}}
```

### Funcoes de Datas

**Localizacao:** `src/adb/core/utils/dates.py`

> **Nota:** Funcoes de uso interno, mas disponiveis para casos especiais.

#### parse_date(date)

Normaliza formatos de data para ISO 8601.

| Entrada | Saida |
|---------|-------|
| '2020' | '2020-01-01' |
| '2020-06' | '2020-06-01' |
| '2020-06-15' | '2020-06-15' |

```python
from adb.core.utils import parse_date

parse_date('2020')      # '2020-01-01'
parse_date('2020-06')   # '2020-06-01'
```

#### normalize_index(df)

Padroniza indice datetime do DataFrame.

- Converte coluna de data para DatetimeIndex
- Remove componente de hora (normaliza para meia-noite)
- Define nome do indice como 'date'

```python
from adb.core.utils import normalize_index

df = normalize_index(df)
# DataFrame com DatetimeIndex padronizado
```

#### DATE_COLUMNS

Lista de nomes reconhecidos como coluna de data:
`['date', 'Date', 'data', 'Data', 'DATE']`

---

> Para diagramas de hierarquia de classes e fluxo de dados, consulte [architecture.md](architecture.md).
