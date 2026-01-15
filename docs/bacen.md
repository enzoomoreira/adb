# Modulo BCB (Banco Central do Brasil)

Documentacao dos coletores de dados do Banco Central: SGS e Expectations.

## Visao Geral

O modulo `src/bacen/` contem dois coletores principais:

| Coletor | Fonte | Descricao |
|---------|-------|-----------|
| SGSCollector | API SGS | Series temporais (Selic, CDI, IPCA, cambio, etc) |
| ExpectationsCollector | API Focus | Expectativas de mercado (relatorio Focus) |

Ambos seguem a mesma **API simplificada**:
- **collect()**: Coleta um ou mais indicadores usando configuracao predefinida
- **consolidate()**: Consolida arquivos em DataFrame unico
- **get_status()**: Retorna status dos arquivos salvos

---

## SGSCollector

Coleta series temporais do Sistema Gerenciador de Series do BCB.

### Uso Basico

```python
from src.bacen import SGSCollector

collector = SGSCollector(data_path='data/')

# Coleta de indicadores
results = collector.collect('selic')              # Um indicador
results = collector.collect(['selic', 'cdi'])     # Lista
results = collector.collect()                      # Todos (default='all')

# Consolidacao (gera cdi_anualizado)
results = collector.consolidate()

# Status dos arquivos
collector.get_status()
```

### Metodos

#### collect(indicators='all', save=True, verbose=True)

Coleta um ou mais indicadores da configuracao predefinida.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| indicators | str\|list | 'all', lista ou string unica |
| save | bool | Salvar em Parquet |
| verbose | bool | Imprimir progresso |

**Retorno:** dict[str, DataFrame]

#### consolidate(subdirs=None, output_prefix=None, save=True, verbose=True)

Consolida arquivos de subdiretorios. Para dados diarios, adiciona coluna `cdi_anualizado`.

**Formula CDI anualizado:**
```
cdi_anualizado = ((1 + cdi_diario/100) ** 252 - 1) * 100
```

**Retorno:** dict[str, DataFrame] com dados consolidados

### Metodos Herdados de BaseCollector

SGSCollector herda funcionalidades comuns de `BaseCollector`:
- `get_status()` - Status dos arquivos salvos
- `_normalize_indicators_list()` - Normaliza entrada de indicadores
- `_normalize_subdirs_list()` - Normaliza entrada de subdirs
- `_log_collect_start()`, `_log_collect_end()` - Banners padronizados de coleta
- `_log_consolidate_start()` - Banner de consolidacao
- `_save_parquet_to_processed()` - Salva em processed/
- `_collect_with_sync()` - Template para coleta incremental

Ver [utils.md](utils.md) para documentacao completa de BaseCollector.

### SGS_CONFIG

Indicadores disponiveis em `src/bacen/sgs/indicators.py`:

| Chave | Codigo | Nome | Frequencia |
|-------|--------|------|------------|
| selic | 432 | Meta Selic | daily |
| cdi | 12 | CDI | daily |
| dolar_ptax | 10813 | Dolar PTAX | daily |
| euro_ptax | 21619 | Euro PTAX | daily |
| ibc_br_bruto | 24363 | IBC-Br Bruto | monthly |
| ibc_br_dessaz | 24364 | IBC-Br Dessazonalizado | monthly |
| igp_m | 189 | IGP-M | monthly |

### Funcoes Auxiliares

**Nota:** As funcoes auxiliares agora sao fornecidas pelo modulo centralizado `core`.

```python
from src.bacen import SGS_CONFIG
from core import list_indicators, get_indicator_config, filter_by_field

list_indicators(SGS_CONFIG)                  # Lista chaves disponiveis
get_indicator_config(SGS_CONFIG, 'selic')    # Retorna config do indicador
filter_by_field(SGS_CONFIG, 'frequency', 'daily')  # Filtra por frequencia
```

---

## ExpectationsCollector

Coleta expectativas de mercado do Relatorio Focus.

### Uso Basico

```python
from src.bacen import ExpectationsCollector

collector = ExpectationsCollector(data_path='data/')

# Coleta de indicadores
results = collector.collect('ipca_anual')          # Um indicador
results = collector.collect(['ipca_anual', 'selic'])  # Lista
results = collector.collect()                       # Todos

# Consolidacao (adiciona _source por padrao)
results = collector.consolidate(add_source=True)

# Status dos arquivos
collector.get_status()
```

### Metodos

#### collect(indicators='all', start_date=None, limit=None, save=True, verbose=True)

Coleta um ou mais indicadores.

**Retorno:** dict[str, DataFrame]

#### consolidate(subdirs=None, output_prefix='expectations', add_source=True, save=True, verbose=True)

Consolida arquivos. Converte coluna 'Data' para DatetimeIndex para fatiamento temporal.

**Retorno:** dict[str, DataFrame]

### Metodos Herdados de BaseCollector

ExpectationsCollector herda funcionalidades comuns de `BaseCollector`:
- `get_status()` - Status dos arquivos salvos
- `_normalize_indicators_list()` - Normaliza entrada de indicadores
- `_normalize_subdirs_list()` - Normaliza entrada de subdirs
- `_log_collect_start()`, `_log_collect_end()` - Banners padronizados de coleta
- `_log_consolidate_start()` - Banner de consolidacao
- `_save_parquet_to_processed()` - Salva em processed/

Ver [utils.md](utils.md) para documentacao completa de BaseCollector.

### EXPECTATIONS_CONFIG

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

### ENDPOINTS

Endpoints disponiveis da API Focus:

```python
ENDPOINTS = {
    "top5_anuais": "ExpectativasMercadoTop5Anuais",
    "anuais": "ExpectativasMercadoAnuais",
    "mensais": "ExpectativaMercadoMensais",
    "selic": "ExpectativasMercadoSelic",
    "inflacao_12m": "ExpectativasMercadoInflacao12Meses",
    "inflacao_24m": "ExpectativasMercadoInflacao24Meses",
    # ... ver indicators.py para lista completa
}
```

---

## Clients (Baixo Nivel)

### SGSClient

Wrapper direto da API SGS:

```python
from src.bacen import SGSClient

client = SGSClient()
df = client.get_data(code=432, name='Selic', frequency='daily', start_date='2024-01-01')
```

### ExpectationsClient

Wrapper direto da API Focus:

```python
from src.bacen import ExpectationsClient

client = ExpectationsClient()
df = client.query(endpoint_key='selic', indicator='Selic', start_date='2024-01-01')
```

---

## Imports Publicos

```python
from src.bacen import (
    # Collectors
    SGSCollector,
    ExpectationsCollector,

    # Clients
    SGSClient,
    ExpectationsClient,

    # Configuracoes SGS
    SGS_CONFIG,

    # Configuracoes Expectations
    EXPECTATIONS_CONFIG,
    ENDPOINTS,
)

# Funcoes auxiliares (centralizadas em core)
from core import (
    list_indicators,
    get_indicator_config,
    filter_by_field,
    BaseCollector,
    DataManager,
)
```

---

## Arquivos Gerados

```
data/
├── raw/
│   └── bacen/
│       ├── sgs/
│       │   ├── daily/        # selic.parquet, cdi.parquet, etc
│       │   └── monthly/      # ibc_br_bruto.parquet, igp_m.parquet, etc
│       └── expectations/     # ipca_anual.parquet, selic.parquet, etc
└── processed/
    ├── bacen_sgs_daily_consolidated.parquet     # Com cdi_anualizado
    ├── bacen_sgs_monthly_consolidated.parquet
    └── expectations_consolidated.parquet
```
