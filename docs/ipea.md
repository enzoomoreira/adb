# Modulo IPEA (Instituto de Pesquisa Economica Aplicada)

Documentacao do coletor de dados do IPEADATA.

## Visao Geral

O modulo `src/adb/ipea/` coleta series temporais agregadas do IPEADATA.

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

## Arquitetura de Uso

### Para Leitura/Queries (Explorer)

```python
import adb

df = adb.ipea.read('caged_saldo')                  # Leitura simples
df = adb.ipea.read('caged_saldo', start='2020')    # Com filtro de data
df = adb.ipea.read('caged_saldo', 'taxa_desemprego')  # Multiplos
print(adb.ipea.available())                        # Lista indicadores
print(adb.ipea.info('caged_saldo'))                # Info do indicador
```

### Para Coleta de Dados

```python
import adb

adb.ipea.collect()                                 # Todos indicadores
adb.ipea.collect(indicators='caged_saldo')         # Um indicador
adb.ipea.collect(indicators=['caged_saldo', 'taxa_desemprego'])  # Lista
```

---

## IPEA_CONFIG

Indicadores disponiveis em `src/adb/ipea/indicators.py`:

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

### Funcoes Auxiliares

```python
from adb.ipea import IPEA_CONFIG
from adb.core import list_indicators, get_indicator_config, filter_by_field

list_indicators(IPEA_CONFIG)                       # Lista chaves
get_indicator_config(IPEA_CONFIG, 'caged_saldo')   # Config completa
filter_by_field(IPEA_CONFIG, 'frequency', 'monthly')  # Filtra
```

---

## Uso Avancado (Acesso Direto)

Para casos especiais:

```python
# Collector (import direto - uso interno)
from adb.ipea.collector import IPEACollector

collector = IPEACollector()
collector.collect(indicators='caged_saldo')
collector.get_status()

# Client (baixo nivel)
from adb.ipea.client import IPEAClient

client = IPEAClient()
df = client.get_data(code='CAGED12_SALDON12', start_date='2020-01-01')
meta = client.get_metadata(code='CAGED12_SALDON12')
series = client.list_series(keyword='CAGED')
```

### IPEACollector.collect()

```python
def collect(
    indicators: list[str] | str = 'all',
    save: bool = True,
    verbose: bool = True,
) -> None
```

### IPEAClient.get_data()

```python
def get_data(
    code: str,
    name: str = None,
    start_date: str = None,
    verbose: bool = False,
) -> pd.DataFrame
```

### IPEAClient.get_metadata()

```python
def get_metadata(code: str) -> dict
# Retorna: {'name', 'unit', 'frequency', 'source', 'last_update'}
```

---

## Exports Publicos

```python
# Config (exportado do modulo ipea)
from adb.ipea import IPEA_CONFIG

# Funcoes auxiliares (centralizadas em core)
from adb.core import list_indicators, get_indicator_config, filter_by_field

# Interface via explorer (recomendado)
import adb
adb.ipea.read(...)
adb.ipea.collect(...)
adb.ipea.available()
adb.ipea.info(...)
adb.ipea.get_status()
```

---

## Arquivos Gerados

```
data/
└── raw/
    └── ipea/
        └── monthly/
            ├── caged_saldo.parquet
            ├── caged_admissoes.parquet
            ├── caged_desligamentos.parquet
            └── taxa_desemprego.parquet
```

---

## Extensibilidade

Para adicionar novos indicadores IPEA:

```python
# Em src/adb/ipea/indicators.py
IPEA_CONFIG['novo_indicador'] = {
    'code': 'CODIGO_IPEADATA',      # Codigo na API IPEADATA
    'name': 'Nome Legivel',
    'frequency': 'monthly',          # daily, monthly, quarterly
    'description': 'Descricao',
    'unit': 'unidade',
    'source': 'Fonte/Orgao',
}
```

**Descobrindo codigos IPEA:**
```python
from adb.ipea.client import IPEAClient
client = IPEAClient()
series = client.list_series(keyword='desemprego')
print(series)  # DataFrame com codigos e descricoes
```

---

## Dependencias

```bash
pip install ipeadatapy
```
