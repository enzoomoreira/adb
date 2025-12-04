# Arquitetura do Projeto dados-bcb

Documentacao tecnica para referencia rapida. Este documento descreve a estrutura e funcionamento do repositorio.

## Visao Geral

Projeto para coleta e armazenamento de dados economicos do Banco Central do Brasil (BCB). Suporta duas fontes de dados:

1. **SGS** (Sistema Gerenciador de Series Temporais) - Series historicas (Selic, IPCA, cambio, etc)
2. **Expectations** (Relatorio Focus) - Expectativas de mercado

## Estrutura de Pastas

```
dados-bcb/
├── src/
│   ├── bacen/                    # Modulo principal
│   │   ├── __init__.py           # Exports publicos
│   │   ├── base.py               # BaseCollector (classe base)
│   │   ├── sgs/                  # Coleta de series temporais
│   │   │   ├── client.py         # SGSClient - wrapper da API
│   │   │   ├── collector.py      # SGSCollector - orquestrador
│   │   │   └── indicators.py     # SGS_CONFIG - configuracao
│   │   └── expectations/         # Coleta de expectativas
│   │       ├── client.py         # ExpectationsClient - wrapper da API
│   │       ├── collector.py      # ExpectationsCollector - orquestrador
│   │       └── indicators.py     # EXPECTATIONS_CONFIG - configuracao
│   └── data/
│       └── manager.py            # DataManager - persistencia centralizada
├── data/                         # Dados coletados
│   ├── raw/                      # Dados brutos por subdiretorio
│   │   ├── sgs/                  # Series temporais do SGS
│   │   │   ├── daily/            # Series diarias (selic, cdi, ptax)
│   │   │   └── monthly/          # Series mensais (ibc-br, igp-m)
│   │   └── expectations/         # Expectativas do Focus
│   └── processed/                # Dados consolidados
├── notebooks/                    # Jupyter notebooks
├── scripts/                      # Scripts utilitarios
└── docs/                         # Documentacao
```

## Hierarquia de Classes

```
BaseCollector (src/bacen/base.py)
├── SGSCollector (src/bacen/sgs/collector.py)
└── ExpectationsCollector (src/bacen/expectations/collector.py)

DataManager (src/data/manager.py) - usado por composicao em todos os collectors
```

## Componentes Principais

### 1. BaseCollector

Classe base que fornece funcionalidades comuns:

```python
class BaseCollector:
    default_subdir: str           # Subdiretorio padrao ('daily', 'expectations')
    default_consolidate_subdirs: list[str]  # Subdirs para consolidacao

    # Atributos
    data_path: Path               # Caminho para data/
    data_manager: DataManager     # Instancia do gerenciador

    # Metodos herdados
    save(df, filename, subdir=None)      # Salva DataFrame
    read(filename, subdir=None)          # Le DataFrame
    list_files(subdir=None)              # Lista arquivos
    get_status(subdir=None)              # Status dos arquivos
```

### 2. SGSCollector

Coleta series temporais do SGS:

```python
from src.bacen import SGSCollector

collector = SGSCollector(data_path='data/')

# Nivel 1: Controle total
df = collector.collect_series(code=432, filename='selic', frequency='daily')

# Nivel 2: API simplificada
results = collector.collect('selic')              # Um indicador
results = collector.collect(['selic', 'cdi'])     # Lista
results = collector.collect()                      # Todos (default='all')

# Consolidacao
results = collector.consolidate()                  # Todos subdirs (sgs/daily + sgs/monthly)
results = collector.consolidate('sgs/daily')       # Um subdir especifico
```

**Configuracao (SGS_CONFIG):**
```python
SGS_CONFIG = {
    'selic': {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily'},
    'cdi': {'code': 12, 'name': 'CDI', 'frequency': 'daily'},
    'dolar_ptax': {'code': 10813, 'name': 'Dolar PTAX', 'frequency': 'daily'},
    'ibc_br_bruto': {'code': 24363, 'name': 'IBC-Br Bruto', 'frequency': 'monthly'},
    # ...
}
```

### 3. ExpectationsCollector

Coleta expectativas do Relatorio Focus:

```python
from src.bacen import ExpectationsCollector

collector = ExpectationsCollector(data_path='data/')

# Nivel 1: Controle total
df = collector.collect_endpoint(endpoint='selic', filename='selic_exp', indicator='Selic')

# Nivel 2: API simplificada
results = collector.collect('ipca_anual')          # Um indicador
results = collector.collect(['ipca_anual', 'selic'])  # Lista
results = collector.collect()                       # Todos

# Consolidacao (com _source por padrao)
results = collector.consolidate(add_source=True)
```

**Configuracao (EXPECTATIONS_CONFIG):**
```python
EXPECTATIONS_CONFIG = {
    'ipca_anual': {'endpoint': 'top5_anuais', 'indicator': 'IPCA'},
    'selic': {'endpoint': 'selic', 'indicator': 'Selic'},
    'pib_anual': {'endpoint': 'top5_anuais', 'indicator': 'PIB Total'},
    # ...
}
```

### 4. DataManager

Gerenciador centralizado de persistencia:

```python
from src.data import DataManager

dm = DataManager(base_path='data/')

# Operacoes basicas
dm.save(df, filename='selic', subdir='sgs/daily')
df = dm.read(filename='selic', subdir='sgs/daily')
files = dm.list_files(subdir='sgs/daily')

# Operacoes avancadas
dm.append(df, filename, subdir)           # Update incremental
last_date = dm.get_last_date(filename, subdir)

# Consolidacao
df = dm.consolidate(
    subdir='sgs/daily',
    output_filename='sgs_daily_consolidated',
    add_source=False,    # True para adicionar coluna _source
    save=True
)
```

### 5. Clients (SGSClient / ExpectationsClient)

Wrappers de baixo nivel para as APIs:

```python
# SGSClient
client = SGSClient()
df = client.query({'Selic': 432}, start_date='2024-01-01')
df = client.get_historical(code=432, name='Selic', frequency='daily')
df = client.get_incremental(code=432, name='Selic', frequency='daily', last_date=dt)

# ExpectationsClient
client = ExpectationsClient()
df = client.query(endpoint_key='selic', indicator='Selic', start_date='2024-01-01')
df = client.get_selic_expectations(start_date='2024-01-01')
df = client.get_annual_expectations(indicator='IPCA', reference_year=2025)
```

## Fluxo de Dados

```
API BCB (SGS/Expectations)
        │
        ▼
    Client (query/fetch)
        │
        ▼
    Collector (orquestra + logica de negocio)
        │
        ▼
    DataManager (persistencia)
        │
        ▼
    data/raw/{subdir}/*.parquet
        │
        ▼ (consolidate)
    data/processed/*.parquet
```

## Padroes de Uso

### Coleta Inicial (Historico Completo)
```python
collector = SGSCollector('data/')
collector.collect()  # Baixa historico de todos os indicadores
```

### Atualizacao Incremental
```python
collector = SGSCollector('data/')
collector.collect()  # Detecta automaticamente e baixa apenas novos dados
```

### Consolidacao para Analise
```python
collector = SGSCollector('data/')
results = collector.consolidate()
df_daily = results['sgs/daily']      # DataFrame com todas as series diarias
df_monthly = results['sgs/monthly']  # DataFrame com todas as series mensais
```

## Imports Publicos

```python
from src.bacen import (
    # Classes
    BaseCollector,
    SGSCollector,
    SGSClient,
    ExpectationsCollector,
    ExpectationsClient,
    # Configuracoes
    SGS_CONFIG,
    EXPECTATIONS_CONFIG,
    ENDPOINTS,
)

from src.data import DataManager
```

## Formato de Dados

- **Formato**: Parquet (compressao Snappy)
- **Indice**: DatetimeIndex
- **Coluna de valor**: `value` (SGS) ou colunas originais (Expectations)
- **Metadata**: Armazenada em `df.attrs` (sgs_code, endpoint, etc)

## Transformacoes Automaticas

### CDI Anualizado

O CDI vem da API como taxa percentual **diaria** (ex: 0.055% ao dia), enquanto a SELIC ja vem como taxa **anual** (ex: 15% ao ano). Para facilitar comparacoes, o `SGSCollector.consolidate()` adiciona automaticamente a coluna `cdi_anualizado` ao arquivo `sgs_daily_consolidated.parquet`.

**Formula:**
```
cdi_anualizado = ((1 + cdi_diario/100) ** 252 - 1) * 100
```

**Exemplo:**
- CDI diario: 0.055131%
- CDI anualizado: 14.90%
- SELIC: 15.00%
- Diferenca tipica: ~0.10 p.p. (CDI fica ligeiramente abaixo da SELIC meta)

**Colunas em sgs_daily_consolidated.parquet:**
- `cdi` - Taxa diaria original
- `cdi_anualizado` - Taxa anualizada (comparavel com SELIC)
- `selic` - Meta SELIC (ja anualizada)
- `dolar_ptax`, `euro_ptax` - Taxas de cambio

## Extensibilidade

Para adicionar novo indicador SGS:
```python
# Em src/bacen/sgs/indicators.py
SGS_CONFIG['novo_indicador'] = {
    'code': 12345,
    'name': 'Nome do Indicador',
    'frequency': 'daily',  # ou 'monthly'
    'description': 'Descricao',
}
```

Para adicionar novo indicador de Expectations:
```python
# Em src/bacen/expectations/indicators.py
EXPECTATIONS_CONFIG['novo_indicador'] = {
    'endpoint': 'top5_anuais',  # ver ENDPOINTS para opcoes
    'indicator': 'Nome na API',
    'description': 'Descricao',
}
```
