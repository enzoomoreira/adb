# Modulo MTE (Ministerio do Trabalho e Emprego)

Documentacao do coletor de dados do Novo CAGED.

## Visao Geral

O modulo `src/mte/` coleta microdados de emprego formal via FTP do MTE.

| Caracteristica | Valor |
|----------------|-------|
| Fonte | FTP pdet.mte.gov.br |
| Formato origem | 7z -> CSV -> Parquet |
| Periodo | 2020-presente (Novo CAGED) |
| Volume | ~500MB-1GB por mes |
| Atualizacao | Mensal (~2 meses de atraso) |

---

## Arquitetura de Uso

### Para Coleta de Dados

```python
from core.collectors import collect

collect('caged')                                  # Todos indicadores
collect('caged', indicators='cagedmov')           # Um indicador
collect('caged', indicators=['cagedmov', 'cagedfor'])  # Lista
# Retorna: dict[str, int] com contagem de registros
```

### Para Leitura/Queries (Explorer)

```python
from core.data import caged

# Leitura de microdados
df = caged.read('cagedmov')                      # Todos os periodos
df = caged.read('cagedmov', start='2024-01')     # A partir de janeiro/2024
df = caged.read('cagedmov', start='2024-01', end='2024-06')

# Consultas agregadas
df = caged.saldo_mensal()                        # Saldo por mes
df = caged.saldo_por_uf()                        # Saldo por UF
df = caged.saldo_por_setor()                     # Saldo por setor

# Informacoes
print(caged.available_periods())                 # Periodos disponiveis
print(caged.info('cagedmov'))                    # Info do indicador
```

### Queries SQL Diretas

Para queries customizadas, use o QueryEngine:

```python
from core.data import QueryEngine

qe = QueryEngine('data/')

# Leitura com filtros
df = qe.read_glob('cagedmov_2024-*.parquet', subdir='mte/caged')
df = qe.read_glob('cagedmov_*.parquet', subdir='mte/caged',
                  columns=['uf', 'saldomovimentacao'],
                  where="uf = 35")  # SP

# Query SQL com DuckDB
df = qe.sql('''
    SELECT uf, SUM(saldomovimentacao) as saldo
    FROM '{raw}/mte/caged/cagedmov_*.parquet'
    WHERE competenciamov >= '2024-01'
    GROUP BY uf
    ORDER BY saldo DESC
''')
```

Veja [data.md](data.md) para documentacao completa do QueryEngine.

---

## CAGED_CONFIG

Indicadores disponiveis em `src/mte/caged/indicators.py`:

| Chave | Prefixo | Descricao | Inicio |
|-------|---------|-----------|--------|
| cagedmov | CAGEDMOV | Movimentacoes (admissoes e desligamentos) | 2020 |
| cagedfor | CAGEDFOR | Declaracoes fora do prazo | 2020 |
| cagedexc | CAGEDEXC | Exclusoes de movimentacoes | 2020 |

### Funcoes Auxiliares

```python
from src.mte import CAGED_CONFIG
from core import list_indicators, get_indicator_config

list_indicators(CAGED_CONFIG)                    # ['cagedmov', 'cagedfor', 'cagedexc']
get_indicator_config(CAGED_CONFIG, 'cagedmov')   # Config do indicador
```

---

## Uso Avancado (Acesso Direto)

Para casos especiais:

```python
# Collector (import direto - uso interno)
from mte.caged.collector import CAGEDCollector

collector = CAGEDCollector(data_path='data/')
results = collector.collect('cagedmov', max_workers=4)
# Retorna: dict[str, int] com contagem de registros
collector.get_status()

# Client (baixo nivel - download FTP)
from mte.caged.client import CAGEDClient

client = CAGEDClient()
client.connect()
file_path = client.download_to_file(prefix='CAGEDMOV', year=2024, month=10)
files = client.list_files(year=2024)
client.disconnect()
```

### CAGEDCollector.collect()

```python
def collect(
    indicators: list[str] | str = 'all',
    save: bool = True,
    verbose: bool = True,
    max_workers: int = 4,
) -> dict[str, int]
```

**Arquitetura de Coleta:**
1. **Download Paralelo**: ThreadPoolExecutor para baixar multiplos arquivos 7z
2. **Conversao Otimizada**: DuckDB para conversao direta CSV -> Parquet
3. **Resiliencia**: Cada mes salvo imediatamente apos conversao

### CAGEDClient.download_to_file()

```python
def download_to_file(
    prefix: str,
    year: int,
    month: int,
    target_path: Path | str = None,
) -> Path  # Retorna path do arquivo 7z baixado
```

### CAGEDCollector.get_status()

```python
def get_status() -> pd.DataFrame
# Colunas: indicador, ultimo_periodo, status
```

---

## Exports Publicos

```python
# Config (exportado)
from src.mte import CAGED_CONFIG

# Funcoes auxiliares (centralizadas em core)
from core import list_indicators, get_indicator_config

# Interface centralizada (recomendado)
from core.collectors import collect
from core.data import caged
```

---

## Arquivos Gerados

```
data/
└── raw/
    └── mte/
        └── caged/
            ├── cagedmov_2020-01.parquet
            ├── cagedmov_2020-02.parquet
            ├── ...
            ├── cagedmov_2024-10.parquet
            ├── cagedfor_2020-01.parquet
            ├── ...
            └── cagedexc_2020-01.parquet
```

**Estrategia de armazenamento:**
- **Raw**: Arquivos mensais individuais (`{indicador}_{ano}-{mes}.parquet`)
- **Vantagens**:
  - Baixo uso de memoria na coleta
  - Atualizacao incremental simples
  - Query eficiente com DuckDB (glob patterns)

---

## Notas Importantes

1. **Volume de dados**: CAGED tem milhoes de registros. Evite carregar tudo na memoria.
2. **Use Explorers/QueryEngine**: Para queries eficientes sem carregar dados.
3. **Separacao de responsabilidades**: Collector baixa dados, Explorer/QueryEngine consulta.
