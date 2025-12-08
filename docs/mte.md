# Modulo MTE (Ministerio do Trabalho e Emprego)

Documentacao do coletor de dados do Novo CAGED.

## Visao Geral

O modulo `src/mte/` coleta microdados de emprego formal via FTP do MTE.

| Caracteristica | Valor |
|----------------|-------|
| Fonte | FTP pdet.mte.gov.br |
| Formato origem | 7z -> CSV |
| Periodo | 2020-presente (Novo CAGED) |
| Volume | ~500MB-1GB por mes |
| Atualizacao | Mensal (~2 meses de atraso) |

---

## CAGEDCollector

Orquestra a coleta de microdados do CAGED com suporte a downloads paralelos.

### Uso Basico

```python
from src.mte import CAGEDCollector

collector = CAGEDCollector(data_path='data/')

# Coleta (paralelo por padrao)
results = collector.collect('cagedmov')            # Um indicador
results = collector.collect(['cagedmov', 'cagedfor'])  # Lista
results = collector.collect()                       # Todos (default='all')
# Retorna: dict[str, int] com contagem de registros

# Leitura com filtros
df = collector.read('cagedmov', year=2024)
df = collector.read('cagedmov', year=[2023, 2024], months=[1, 2, 3])
df = collector.read('cagedmov', columns=['uf', 'saldomovimentacao'])

# Query SQL com DuckDB
df = collector.query('''
    SELECT uf, COUNT(*) as total
    FROM 'data/raw/mte/caged/cagedmov_2024-*.parquet'
    GROUP BY uf
''')

# Status
collector.get_status()
```

### Metodos

#### collect(indicators='all', save=True, verbose=True, parallel=True, max_workers=4)

Coleta dados do CAGED. Salva arquivos mensais individuais para evitar MemoryError.

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| indicators | str\|list | 'all' | Indicadores a coletar |
| save | bool | True | Salvar em Parquet |
| verbose | bool | True | Imprimir progresso |
| parallel | bool | True | Baixar em paralelo |
| max_workers | int | 4 | Numero de threads |

**Retorno:** dict[str, int] com contagem de registros por indicador

**Observacoes:**
- Cada mes e salvo imediatamente apos download (baixo uso de memoria)
- Se falhar no meio, meses ja salvos permanecem (resiliencia)
- Downloads paralelos usam conexoes FTP independentes por thread

#### read(indicator='cagedmov', year=None, months=None, columns=None)

Le dados do CAGED com filtros opcionais.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| indicator | str | cagedmov, cagedfor, cagedexc |
| year | int\|list | Ano(s) para filtrar |
| months | list | Meses para filtrar |
| columns | list | Colunas para carregar |

**Retorno:** DataFrame concatenado

#### get_files(indicator='cagedmov', year=None)

Retorna lista de paths dos arquivos parquet. Util para uso com DuckDB, PyArrow, etc.

**Retorno:** list[Path]

#### query(sql)

Executa query SQL nos arquivos parquet usando DuckDB.

```python
# Agregacao por UF
df = collector.query('''
    SELECT uf, SUM(saldomovimentacao) as saldo
    FROM 'data/raw/mte/caged/cagedmov_*.parquet'
    WHERE competenciamov >= '2024-01'
    GROUP BY uf
    ORDER BY saldo DESC
''')
```

**Requer:** `pip install duckdb`

#### get_status()

Retorna DataFrame com status dos dados locais (ultimo periodo baixado).

---

## CAGED_CONFIG

Indicadores disponiveis em `src/mte/caged/indicators.py`:

| Chave | Prefixo | Descricao | Inicio |
|-------|---------|-----------|--------|
| cagedmov | CAGEDMOV | Movimentacoes (admissoes e desligamentos) | 2020 |
| cagedfor | CAGEDFOR | Declaracoes fora do prazo | 2020 |
| cagedexc | CAGEDEXC | Exclusoes de movimentacoes | 2020 |

---

## CAGEDClient

Cliente FTP de baixo nivel para download e extracao de arquivos.

```python
from src.mte import CAGEDClient

client = CAGEDClient()
client.connect()

# Baixa e extrai arquivo 7z automaticamente
df = client.get_data(prefix='CAGEDMOV', year=2024, month=10)

# Lista arquivos disponiveis no FTP
files = client.list_files(year=2024)

client.disconnect()
```

---

## Funcoes Auxiliares

```python
from src.mte import (
    CAGED_CONFIG,
    list_indicators,
    get_indicator_config,
    get_available_periods,
)

list_indicators()                    # ['cagedmov', 'cagedfor', 'cagedexc']
get_indicator_config('cagedmov')     # Retorna config do indicador
get_available_periods(start_year=2023)  # Lista (ano, mes) disponiveis
```

---

## Imports Publicos

```python
from src.mte import (
    # Collector
    CAGEDCollector,

    # Client
    CAGEDClient,

    # Configuracoes
    CAGED_CONFIG,
    list_indicators,
    get_indicator_config,
    get_available_periods,
)
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
2. **DuckDB**: Use `query()` para agregacoes eficientes sem carregar dados.
3. **Filtros**: Use `read()` com filtros de ano/mes para limitar dados carregados.
4. **Parallelismo**: Downloads paralelos reduzem tempo significativamente (~4x mais rapido).
