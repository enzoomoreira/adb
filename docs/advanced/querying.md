# Queries Avancadas

Guia para power users sobre queries avancadas usando o `QueryEngine` diretamente.

## Visao Geral

O `QueryEngine` e o motor de consultas SQL do projeto, baseado em **DuckDB**. Enquanto os explorers fornecem uma interface de alto nivel (`adb.sgs.read()`), o QueryEngine permite queries SQL arbitrarias diretamente sobre os arquivos Parquet.

## Quando Usar

| Cenario | Explorer | QueryEngine |
|---------|----------|-------------|
| Leitura simples de indicadores | Sim | - |
| Filtros por periodo | Sim | - |
| SQL customizado com JOINs | - | Sim |
| Agregacoes complexas | - | Sim |
| Leitura de multiplos arquivos com glob | - | Sim |
| Performance critica | - | Sim |

## Import e Inicializacao

```python
from adb.infra.query import QueryEngine

# Inicializacao padrao (usa get_settings().data_dir)
qe = QueryEngine()

# Com path customizado
qe = QueryEngine(base_path='/path/to/data')

# Com barra de progresso para queries longas
qe = QueryEngine(progress_bar=True)
```

## Metodos Disponiveis

| Metodo | Descricao |
|--------|-----------|
| `read(filename, subdir, columns, where)` | Le arquivo unico com filtros |
| `read_glob(pattern, subdir, columns, where)` | Le multiplos arquivos |
| `sql(query, subdir)` | SQL arbitrario |
| `aggregate(filename, subdir, group_by, agg, where)` | Agregacoes |
| `get_metadata(filename, subdir)` | Metadados do arquivo |
| `connection()` | Conexao DuckDB configurada |

---

## Leitura Basica com Filtros WHERE

### Sintaxe

```python
df = qe.read(
    filename='selic',           # Nome do arquivo (sem .parquet)
    subdir='bacen/sgs/daily',   # Subdiretorio em data/
    columns=['date', 'value'],  # Colunas (opcional, None = todas)
    where="date >= '2023-01-01'"  # Filtro SQL (opcional)
)
```

### Exemplos de Filtros WHERE

```python
# Filtro por data
df = qe.read('selic', 'bacen/sgs/daily',
             where="date >= '2023-01-01'")

# Filtro por intervalo
df = qe.read('selic', 'bacen/sgs/daily',
             where="date BETWEEN '2023-01-01' AND '2023-12-31'")

# Filtro por valor
df = qe.read('selic', 'bacen/sgs/daily',
             where="value > 10.0")

# Filtros combinados
df = qe.read('selic', 'bacen/sgs/daily',
             where="date >= '2023-01-01' AND value > 10.0")

# Filtro com IN
df = qe.read('ipca', 'ibge/sidra',
             where="nivel_territorial IN ('N1', 'N2', 'N3')")

# Filtro com LIKE
df = qe.read('ipca', 'ibge/sidra',
             where="descricao LIKE '%Alimentacao%'")
```

### Selecao de Colunas

```python
# Colunas especificas
df = qe.read('selic', 'bacen/sgs/daily', columns=['date', 'value'])

# Todas as colunas (default)
df = qe.read('selic', 'bacen/sgs/daily')
```

> **Nota:** O QueryEngine inclui automaticamente a coluna de data se ela existir no arquivo, mesmo quando voce nao especifica.

---

## Leitura com Glob Patterns

O metodo `read_glob()` permite ler multiplos arquivos que correspondem a um padrao.

### Sintaxe

```python
df = qe.read_glob(
    pattern='selic_*.parquet',            # Glob pattern
    subdir='bacen/sgs/daily',             # Subdiretorio
    columns=['date', 'value'],            # Colunas (opcional)
    where="date >= '2024-01-01'"          # Filtro SQL (opcional)
)
```

### Padroes Glob Comuns

| Padrao | Descricao |
|--------|-----------|
| `*.parquet` | Todos os arquivos Parquet |
| `selic_*.parquet` | Todos os arquivos Selic |
| `expectativas_*.parquet` | Todas as expectativas |

### Exemplos Praticos

```python
# Ler todas as series mensais do SGS
df = qe.read_glob(
    '*.parquet',
    subdir='bacen/sgs/monthly'
)

# Combinar com filtro de data
df = qe.read_glob(
    '*.parquet',
    subdir='bacen/sgs/daily',
    where="date >= '2023-01-01'"
)
```

---

## SQL Arbitrario

O metodo `sql()` permite executar qualquer query DuckDB valida.

### Variaveis de Path

O QueryEngine substitui automaticamente estas variaveis:

| Variavel | Caminho |
|----------|---------|
| `{base}` | `data/` |
| `{subdir}` | `data/{subdir_param}/` (se passado) |

### Exemplos

```python
# Query simples com variavel
df = qe.sql("""
    SELECT date, value
    FROM '{base}/bacen/sgs/daily/selic.parquet'
    WHERE date >= '2023-01-01'
""")

# JOIN entre arquivos
df = qe.sql("""
    SELECT s.date, s.value as selic, c.value as cdi
    FROM '{base}/bacen/sgs/daily/selic.parquet' s
    JOIN '{base}/bacen/sgs/daily/cdi.parquet' c
      ON s.date = c.date
    WHERE s.date >= '2020-01-01'
""")

# Usando subdir para simplificar
df = qe.sql("""
    SELECT date, value
    FROM '{subdir}/selic.parquet'
    WHERE date >= '2023-01-01'
""", subdir='bacen/sgs/daily')

# Glob no SQL
df = qe.sql("""
    SELECT *
    FROM '{base}/bacen/sgs/daily/*.parquet'
    WHERE date >= '2024-01-01'
""")

# Subquery e CTE
df = qe.sql("""
    WITH monthly_avg AS (
        SELECT
            DATE_TRUNC('month', date) as month,
            AVG(value) as avg_selic
        FROM '{base}/bacen/sgs/daily/selic.parquet'
        WHERE date >= '2020-01-01'
        GROUP BY DATE_TRUNC('month', date)
    )
    SELECT *
    FROM monthly_avg
    ORDER BY month
""")
```

---

## Agregacoes

O metodo `aggregate()` simplifica agregacoes comuns sem escrever SQL.

### Sintaxe

```python
df = qe.aggregate(
    filename='selic',
    subdir='bacen/sgs/daily',
    group_by='YEAR(date)',       # Coluna(s) de agrupamento
    agg={'value': 'AVG'},        # {coluna: funcao}
    where="date >= '2020-01-01'" # Filtro (opcional)
)
```

### Funcoes de Agregacao Suportadas

| Funcao | Descricao |
|--------|-----------|
| `AVG` | Media |
| `SUM` | Soma |
| `MIN` | Minimo |
| `MAX` | Maximo |
| `COUNT` | Contagem |
| `COUNT(DISTINCT col)` | Contagem distinta |
| `STDDEV` | Desvio padrao |
| `VAR` | Variancia |

### Exemplos

```python
# Media anual da Selic
df = qe.aggregate(
    'selic', 'bacen/sgs/daily',
    group_by='YEAR(date)',
    agg={'value': 'AVG'}
)

# Multiplas agregacoes
df = qe.aggregate(
    'selic', 'bacen/sgs/daily',
    group_by='YEAR(date)',
    agg={'value': 'AVG', 'value': 'MAX'}  # Ultimo ganha
)

# Agrupamento por multiplas colunas
df = qe.aggregate(
    'ipca', 'ibge/sidra',
    group_by=['nivel_territorial', 'variavel'],
    agg={'value': 'AVG'},
    where="date >= '2023-01-01'"
)

# Agregacao mensal
df = qe.aggregate(
    'selic', 'bacen/sgs/daily',
    group_by="DATE_TRUNC('month', date)",
    agg={'value': 'AVG'},
    where="date >= '2023-01-01'"
)
```

---

## Conexao DuckDB Direta

Para queries muito complexas ou uso de recursos avancados do DuckDB:

```python
# Obter conexao configurada
con = qe.connection()

# Usar diretamente
result = con.execute("""
    SELECT *
    FROM read_parquet(getvariable('base_path') || '/bacen/sgs/daily/*.parquet')
""").fetchdf()

# Registrar tabela virtual
con.execute("""
    CREATE OR REPLACE VIEW selic AS
    SELECT * FROM read_parquet('data/bacen/sgs/daily/selic.parquet')
""")

# Usar a view
df = con.execute("SELECT * FROM selic WHERE date >= '2023-01-01'").fetchdf()
```

---

## Metadados de Arquivos

```python
# Obter informacoes sobre um arquivo
meta = qe.get_metadata('selic', 'bacen/sgs/daily')
print(meta)
# {
#     'arquivo': 'selic',
#     'subdir': 'bacen/sgs/daily',
#     'registros': 8520,
#     'colunas': 2,
#     'primeira_data': Timestamp('2000-01-03'),
#     'ultima_data': Timestamp('2025-01-15'),
#     'status': 'OK'
# }
```

---

## Exemplos de Queries Complexas

### Media Movel de 21 Dias

```python
df = qe.sql("""
    SELECT
        date,
        value,
        AVG(value) OVER (
            ORDER BY date
            ROWS BETWEEN 20 PRECEDING AND CURRENT ROW
        ) as mm21
    FROM '{base}/bacen/sgs/daily/selic.parquet'
    WHERE date >= '2020-01-01'
    ORDER BY date
""")
```

### Variacao Percentual Mensal

```python
df = qe.sql("""
    SELECT
        DATE_TRUNC('month', date) as month,
        LAST(value ORDER BY date) as last_value,
        FIRST(value ORDER BY date) as first_value,
        (LAST(value ORDER BY date) / FIRST(value ORDER BY date) - 1) * 100 as var_pct
    FROM '{base}/bacen/sgs/daily/dolar_ptax.parquet'
    WHERE date >= '2020-01-01'
    GROUP BY DATE_TRUNC('month', date)
    ORDER BY month
""")
```

### Correlacao Entre Series

```python
df = qe.sql("""
    SELECT
        CORR(s.value, c.value) as corr_selic_cdi,
        CORR(s.value, d.value) as corr_selic_dolar
    FROM '{base}/bacen/sgs/daily/selic.parquet' s
    JOIN '{base}/bacen/sgs/daily/cdi.parquet' c ON s.date = c.date
    JOIN '{base}/bacen/sgs/daily/dolar_ptax.parquet' d ON s.date = d.date
    WHERE s.date >= '2020-01-01'
""")
```

### Ranking por Valor Medio Anual

```python
df = qe.sql("""
    SELECT
        YEAR(date) as year,
        AVG(value) as avg_value,
        RANK() OVER (ORDER BY AVG(value) DESC) as ranking
    FROM '{base}/bacen/sgs/daily/dolar_ptax.parquet'
    WHERE date >= '2015-01-01'
    GROUP BY YEAR(date)
    ORDER BY ranking
""")
```

---

## Performance Tips

1. **Sempre use filtros WHERE** - DuckDB faz pushdown de predicados, lendo apenas partitions necessarias

2. **Selecione apenas colunas necessarias** - Parquet e columnar, colunas nao usadas nao sao lidas

3. **Prefira `read()` sobre `sql()` para queries simples** - Menos overhead de parsing

4. **Use glob patterns ao inves de UNION** - DuckDB otimiza leitura de multiplos arquivos

5. **Considere `progress_bar=True`** para queries longas - Ajuda a acompanhar progresso

```python
# Bom: Filtros e colunas especificas
df = qe.read('selic', 'bacen/sgs/daily',
             columns=['date', 'value'],
             where="date >= '2023-01-01'")

# Evitar: Ler tudo e filtrar depois em pandas
df = qe.read('selic', 'bacen/sgs/daily')
df = df[df['date'] >= '2023-01-01'][['date', 'value']]
```

---

## Proximos Passos

- [Estendendo o Projeto](extending.md) - Como adicionar novos providers e indicadores
- [Documentacao DuckDB](https://duckdb.org/docs/) - Referencia completa de SQL
