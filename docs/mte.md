# Modulo MTE (Ministerio do Trabalho e Emprego)

Documentacao do coletor de dados do Novo CAGED.

## Visao Geral

O modulo `src/mte/` coleta microdados de emprego formal via FTP do MTE.

| Caracteristica | Valor |
|----------------|-------|
| Fonte | FTP ftp.mtps.gov.br |
| Formato origem | 7z -> CSV -> Parquet |
| Periodo | 2020-presente (Novo CAGED) |
| Volume | ~500MB-1GB por mes |
| Atualizacao | Mensal (~2 meses de atraso) |

---

## Arquitetura de Uso

### Para Coleta de Dados

```python
from core.collectors import collect

collect('caged')                                   # Todos indicadores, todos periodos
collect('caged', indicators='cagedmov')            # Um indicador
collect('caged', indicators=['cagedmov', 'cagedfor'])  # Lista de indicadores
# Retorna: dict[str, int] com contagem de registros por indicador
```

### Para Leitura/Queries (Explorer)

```python
from core.data import caged

# Leitura de microdados (year obrigatorio)
df = caged.read(year=2024)                       # Ano inteiro
df = caged.read(year=2024, month=6)              # Mes especifico
df = caged.read(year=2024, uf=35)                # Filtrado por UF (SP)
df = caged.read(year=2024, dataset='cagedfor')   # Outro dataset

# Consultas agregadas (year obrigatorio)
df = caged.saldo_mensal(year=2024)               # Saldo por mes
df = caged.saldo_por_uf(year=2024)               # Saldo por UF
df = caged.saldo_por_setor(year=2024)            # Saldo por setor

# Informacoes
print(caged.available_periods())                 # Periodos disponiveis
print(caged.info('cagedmov'))                    # Info do indicador
```

### Queries SQL Diretas

Para queries customizadas, use o QueryEngine:

```python
from core.data import QueryEngine

qe = QueryEngine()  # Usa DATA_PATH padrao

# Leitura com filtros
df = qe.read_glob('cagedmov_2024-*.parquet', subdir='mte/caged')
df = qe.read_glob('cagedmov_*.parquet', subdir='mte/caged',
                  columns=['uf', 'saldomovimentacao'],
                  where="uf = 35")  # SP

# Query SQL com DuckDB (usa {raw} como variavel)
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
from mte import CAGED_CONFIG
from core.utils import list_indicators, get_indicator_config

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
from mte import CAGED_CONFIG

# Funcoes auxiliares (centralizadas em core.utils)
from core.utils import list_indicators, get_indicator_config

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
