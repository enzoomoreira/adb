# Modulo IPEA (Instituto de Pesquisa Economica Aplicada)

Documentacao do coletor de dados do IPEADATA.

## Visao Geral

O modulo `src/ipea/` coleta series temporais agregadas do IPEADATA.

| Caracteristica | Valor |
|----------------|-------|
| Fonte | API IPEADATA (via ipeadatapy) |
| Formato | Series temporais |
| Foco atual | Dados agregados de emprego (CAGED, PNAD) |

**Por que usar IPEA?**
- Dados agregados (saldo, admissoes, desligamentos) sem precisar processar microdados
- Complementa os microdados do CAGED com visao macro
- Inclui taxa de desemprego (PNAD Continua)

---

## IPEACollector

Orquestra a coleta de series temporais do IPEADATA.

### Uso Basico

```python
from src.ipea import IPEACollector

collector = IPEACollector(data_path='data/')

# Coleta de indicadores
results = collector.collect('caged_saldo')              # Um indicador
results = collector.collect(['caged_saldo', 'taxa_desemprego'])  # Lista
results = collector.collect()                            # Todos (default='all')

# Consolidacao
df = collector.consolidate()

# Status
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

#### consolidate(subdir='ipea/monthly', output_filename='ipea_monthly_consolidated', save=True, verbose=True)

Consolida arquivos de um subdiretorio via join horizontal por indice (data).

**Retorno:** DataFrame consolidado

#### get_status(subdir='ipea/monthly')

Retorna status dos arquivos salvos (registros, datas, status).

**Retorno:** DataFrame

### Metodos Herdados de BaseCollector

IPEACollector herda funcionalidades comuns de `BaseCollector`:
- `get_status()` - Status dos arquivos salvos
- `_normalize_indicators_list()` - Normaliza entrada de indicadores
- `_log_collect_start()`, `_log_collect_end()` - Banners padronizados de coleta
- `_log_consolidate_start()` - Banner de consolidacao
- `_collect_with_sync()` - Template para coleta incremental

Ver [utils.md](utils.md) para documentacao completa de BaseCollector.

---

## IPEA_CONFIG

Indicadores disponiveis em `src/ipea/indicators.py`:

### Emprego (CAGED Agregado)

| Chave | Codigo | Nome | Unidade |
|-------|--------|------|---------|
| caged_saldo | CAGED12_SALDON12 | Saldo do Novo CAGED | pessoas |
| caged_admissoes | CAGED12_ADMISN12 | Admissoes CAGED | pessoas |
| caged_desligamentos | CAGED12_DESLIGN12 | Desligamentos CAGED | pessoas |

### Desemprego (PNAD)

| Chave | Codigo | Nome | Unidade |
|-------|--------|------|---------|
| taxa_desemprego | PNADC12_TDESOC12 | Taxa de Desocupacao | % |

---

## IPEAClient

Cliente de baixo nivel para API IPEADATA (wrapper do ipeadatapy).

```python
from src.ipea import IPEAClient

client = IPEAClient()

# Busca serie temporal
df = client.get_data(code='CAGED12_SALDON12', start_date='2020-01-01')

# Metadados da serie
meta = client.get_metadata(code='CAGED12_SALDON12')
# Retorna: {'name': ..., 'unit': ..., 'frequency': ..., 'source': ...}

# Listar series disponiveis
series = client.list_series(keyword='CAGED')
```

**Normalizacao:**
- Saida padronizada: DatetimeIndex (sem timezone) + coluna 'value'
- Compativel com o padrao do projeto (igual ao SGS)

---

## Funcoes Auxiliares

**Nota:** As funcoes auxiliares agora sao fornecidas pelo modulo centralizado `core`.

```python
from src.ipea import IPEA_CONFIG
from core import list_indicators, get_indicator_config, filter_by_field

list_indicators(IPEA_CONFIG)                     # Lista chaves disponiveis
get_indicator_config(IPEA_CONFIG, 'caged_saldo') # Retorna config completa
filter_by_field(IPEA_CONFIG, 'frequency', 'monthly')  # Filtra por frequencia
```

---

## Imports Publicos

```python
from src.ipea import (
    # Collector
    IPEACollector,

    # Client
    IPEAClient,

    # Configuracoes
    IPEA_CONFIG,
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
│   └── ipea/
│       └── monthly/
│           ├── caged_saldo.parquet
│           ├── caged_admissoes.parquet
│           ├── caged_desligamentos.parquet
│           └── taxa_desemprego.parquet
└── processed/
    └── ipea_monthly_consolidated.parquet
```

---

## Extensibilidade

Para adicionar novos indicadores IPEA:

```python
# Em src/ipea/indicators.py
IPEA_CONFIG['novo_indicador'] = {
    'code': 'CODIGO_IPEADATA',      # Codigo na API IPEADATA
    'name': 'Nome Legivel',         # Nome para logs
    'frequency': 'monthly',          # daily, monthly, quarterly
    'description': 'Descricao',     # O que o indicador representa
    'unit': 'unidade',              # Unidade de medida
    'source': 'Fonte/Orgao',        # Fonte original dos dados
}
```

**Descobrindo codigos IPEA:**
```python
client = IPEAClient()
series = client.list_series(keyword='desemprego')  # Busca por palavra-chave
print(series)  # DataFrame com codigos e descricoes
```

---

## Dependencias

- **ipeadatapy**: Biblioteca oficial para acesso ao IPEADATA
  ```bash
  pip install ipeadatapy
  ```
