# Modulo Core Data - Persistencia e Consultas

Documentacao do gerenciador centralizado de persistencia e consultas SQL.

## Visao Geral

O modulo `src/core/data/` contem dois componentes principais:

| Componente | Arquivo | Descricao |
|------------|---------|-----------|
| DataManager | `storage.py` | Persistencia de dados em Parquet (save, read, append) |
| QueryEngine | `query.py` | Consultas SQL via DuckDB em arquivos Parquet |

Alem disso, o modulo expoe **Explorers** para cada fonte de dados via lazy loading.

---

## Explorers (Interface Principal)

A forma recomendada de ler dados e via Explorers:

```python
from core.data import sgs, expectations, caged, ipea, bloomberg

# Leitura simples
df = sgs.read('selic')
df = expectations.read('ipca_anual')
df = ipea.read('caged_saldo')
df = bloomberg.read('brent')

# Com filtros de data
df = sgs.read('selic', start='2020')
df = sgs.read('selic', start='2020', end='2024')

# Multiplos indicadores
df = sgs.read('selic', 'cdi')

# Informacoes
print(sgs.available())           # Lista indicadores
print(sgs.info('selic'))         # Info do indicador

# CAGED (microdados) - interface diferente
df = caged.read(year=2025)                    # Todos os meses
df = caged.read(year=2025, month=10)          # Mes especifico
df = caged.read(year=2025, uf=35)             # Filtrar por UF

# CAGED - agregacoes (year obrigatorio)
df = caged.saldo_mensal(year=2025)
df = caged.saldo_por_uf(year=2025)
df = caged.saldo_por_setor(year=2025)
print(caged.available_periods())
print(caged.info('cagedmov'))
```

---

# DataManager (storage.py)

API unificada para salvar e ler dados em formato Parquet. Usado internamente por todos os collectors.

## Inicializacao

```python
from core.data import DataManager

dm = DataManager(base_path='data/')

# Atributos disponiveis
dm.base_path       # Path('data/')
dm.raw_path        # Path('data/raw/')
dm.processed_path  # Path('data/processed/')
```

## Metodos Principais

### save(df, filename, subdir='daily', format='parquet', metadata=None, verbose=False)

Salva DataFrame em arquivo.

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| df | DataFrame | - | Dados para salvar |
| filename | str | - | Nome do arquivo (sem extensao) |
| subdir | str | 'daily' | Subdiretorio dentro de raw/ |
| format | str | 'parquet' | 'parquet' ou 'csv' |
| metadata | dict | None | Metadata adicional |
| verbose | bool | False | Imprimir caminho |

```python
dm.save(df, filename='selic', subdir='bacen/sgs/daily')
# Salva em: data/raw/bacen/sgs/daily/selic.parquet
```

### read(filename, subdir='daily')

Le arquivo de dados.

**Retorno:** DataFrame (vazio se arquivo nao existe)

```python
df = dm.read(filename='selic', subdir='bacen/sgs/daily')
```

### append(df, filename, subdir='daily', dedup=True, verbose=False)

Adiciona novos dados a arquivo existente (update incremental).

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| dedup | bool | True | Remover duplicatas por indice |

**Comportamento dedup:**
- `dedup=True`: Para series temporais (indice = data). Remove duplicatas mantendo valor mais recente.
- `dedup=False`: Para microdados (cada linha e unica). Usa `ignore_index=True`.

```python
# Series temporal (dedup por data)
dm.append(novos_dados, 'selic', 'bacen/sgs/daily', dedup=True)

# Microdados (sem dedup)
dm.append(novos_registros, 'cagedmov', 'mte/caged', dedup=False)
```

### list_files(subdir='daily')

Lista arquivos salvos em um subdiretorio.

**Retorno:** Lista de nomes (sem extensao)

```python
arquivos = dm.list_files('bacen/sgs/daily')
# ['selic', 'cdi', 'dolar_ptax', ...]
```

### get_last_date(filename, subdir='daily')

Retorna ultima data disponivel em um arquivo.

**Retorno:** datetime ou None

```python
ultima = dm.get_last_date('selic', 'bacen/sgs/daily')
# datetime(2024, 12, 6)
```

### is_first_run(subdir)

Verifica se e primeira execucao (subdiretorio vazio ou inexistente).

**Retorno:** bool

### get_file_path(filename, subdir)

Retorna o path completo de um arquivo.

**Retorno:** Path

### get_metadata(filename, subdir='daily')

Retorna metadados de um arquivo.

**Retorno:** dict ou None (se arquivo nao existe)

---

# QueryEngine (query.py)

Motor de consultas SQL otimizado para arquivos Parquet usando DuckDB.

## Visao Geral

O `QueryEngine` e o mecanismo principal de leitura do projeto. Abstrai o DuckDB para permitir consultas SQL diretas em arquivos Parquet.

**Principais Features:**
- **DuckDB-first:** Utiliza DuckDB para todas as leituras, garantindo performance superior.
- **Pushdown Optimization:** Aplica filtros (`WHERE`) e selecao de colunas antes de carregar dados.
- **Glob Support:** Le diretorios inteiros (`*.parquet`) como tabela unica.
- **Date Normalization:** Garante consistencia de indices temporais.

## Inicializacao

```python
from core.data import QueryEngine

qe = QueryEngine(base_path='data/')
```

## Metodos Principais

### read(filename, subdir='daily', columns=None, where=None)

Le um arquivo Parquet de forma eficiente.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| filename | str | Nome do arquivo (sem extensao) |
| subdir | str | Subdiretorio (ex: 'bacen/sgs/daily') |
| columns | list | Selecao de colunas (None = todas) |
| where | str | Filtro SQL (ex: "value > 10") |

```python
# Leitura simples
df = qe.read('selic', 'bacen/sgs/daily')

# Leitura otimizada
df = qe.read(
    'cagedmov_202401',
    'mte/caged',
    columns=['uf', 'saldomovimentacao'],
    where="uf = 35"
)
```

### read_glob(pattern, subdir=None, columns=None, where=None)

Le multiplos arquivos que correspondem a um padrao.

```python
# Le todo historico do CAGED de 2024
df = qe.read_glob('cagedmov_2024*.parquet', subdir='mte/caged')

# Com filtros
df = qe.read_glob(
    'cagedmov_*.parquet',
    subdir='mte/caged',
    columns=['uf', 'saldomovimentacao'],
    where="uf = 35"
)
```

### sql(query, subdir=None)

Executa SQL arbitrario do DuckDB. Suporta variaveis de template `{raw}` e `{processed}`.

```python
df = qe.sql("""
    SELECT uf, SUM(saldomovimentacao) as saldo
    FROM '{raw}/mte/caged/cagedmov_*.parquet'
    GROUP BY uf
    ORDER BY saldo DESC
""")
```

### aggregate(filename, subdir, group_by, agg, where=None)

Executa agregacao otimizada no banco de dados (DuckDB).

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| agg | dict | Dicionario `{coluna: funcao}` (ex: `{'value': 'AVG'}`) |

```python
df = qe.aggregate(
    filename='cagedmov_*.parquet',
    subdir='mte/caged',
    group_by='uf',
    agg={'saldomovimentacao': 'SUM'},
    where="competenciamov >= '2024-01-01'"
)
```

### get_metadata(filename, subdir)

Retorna metadados do arquivo (contagem de linhas, datas e colunas) sem ler o arquivo inteiro.

### connection()

Retorna conexao DuckDB configurada.

**Retorno:** duckdb.DuckDBPyConnection

---

## Estrutura de Diretorios

```
data/
├── raw/                      # Dados brutos (por fonte/tipo)
│   ├── bacen/
│   │   ├── sgs/
│   │   │   ├── daily/       # selic.parquet, cdi.parquet, ...
│   │   │   └── monthly/     # ibc_br_bruto.parquet, ...
│   │   └── expectations/    # ipca_anual.parquet, ...
│   ├── mte/
│   │   └── caged/           # cagedmov_2024-01.parquet, ...
│   ├── ipea/
│   │   └── monthly/         # caged_saldo.parquet, ...
│   └── bloomberg/
│       └── daily/           # brent.parquet, ...
└── processed/               # (Opcional - uso futuro)
```

---

## Comparacao: QueryEngine vs DataManager

| Operacao | DataManager | QueryEngine |
|----------|-------------|-------------|
| **Foco** | I/O (Salvar, Append) | Leitura / Analytics |
| **Backend** | PyArrow / Pandas | DuckDB |
| **Leitura** | `read()` (Arquivo unico) | `read()`, `read_glob()`, `sql()` |
| **Filtros** | Nao suporta | Sim (`where=...`) |
| **Performance** | Padrao | Otimizada (Colunar) |

---

## Formato de Dados

### Parquet

- **Engine:** PyArrow (escrita) / DuckDB (leitura)
- **Compressao:** Snappy
- **Indice:** Preservado (DatetimeIndex) quando aplicavel

### Convencoes

- **Indice:** DatetimeIndex para series temporais (normalizado para naive datetime)
- **Coluna de valor:** `value` (normalizado pelos clients)

---

## Performance Tips

**Filtros pushdown:**
- Use `columns` para carregar apenas colunas necessarias
- Use `where` para filtrar antes de carregar em memoria
- DuckDB aplica otimizacoes automaticamente

**Glob patterns:**
- Eficiente para ler multiplos arquivos particionados
- DuckDB processa em streaming

**Agregacoes:**
- Use `aggregate()` para operacoes de resumo
- Mais rapido que carregar e agregar em pandas

---

## Imports

```python
# Componentes principais
from core.data import DataManager, QueryEngine

# Explorers (recomendado para leitura)
from core.data import sgs, expectations, caged, ipea, bloomberg
```

---

## Dependencias

```bash
pip install duckdb pandas pyarrow
```
