# DataManager - Persistencia de Dados

Documentacao do gerenciador centralizado de persistencia.

## Visao Geral

O `DataManager` fornece API unificada para salvar, ler e consolidar dados em formato Parquet. E usado por todos os collectors do projeto.

**Localização:** `src/core/data/manager.py`

---

## Inicializacao

```python
from src.core.data import DataManager

dm = DataManager(base_path='data/')

# Atributos disponiveis
dm.base_path       # Path('data/')
dm.raw_path        # Path('data/raw/')
dm.processed_path  # Path('data/processed/')
```

---

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

---

## fetch_and_sync() - Sincronizacao Incremental

Metodo centralizado que orquestra coleta incremental de dados.

```python
def fetch_and_sync(
    filename: str,
    subdir: str,
    fetch_fn: Callable[[str | None], pd.DataFrame],
    frequency: str = 'daily',
    verbose: bool = True,
) -> tuple[pd.DataFrame, bool]
```

**Fluxo:**
1. Verifica ultima data salva (`get_last_date`)
2. Calcula `start_date` para proxima busca:
   - Primeira execucao: `None` (historico completo)
   - Daily: dia seguinte
   - Monthly: proximo mes
3. Chama `fetch_fn(start_date)` para obter dados
4. Salva (`save`) ou appenda (`append`) conforme necessario
5. Retorna `(DataFrame, is_first_run)`

**Exemplo de uso:**
```python
def fetch(start_date):
    return client.get_data(code=432, start=start_date)

df, is_first = dm.fetch_and_sync(
    filename='selic',
    subdir='bacen/sgs/daily',
    fetch_fn=fetch,
    frequency='daily'
)
```

**Por que usar:**
- Centraliza logica de coleta incremental
- Evita duplicacao de codigo em cada collector
- Trata automaticamente primeira execucao vs. atualizacao

---

## consolidate() - Consolidacao de Dados

Consolida multiplos arquivos em um DataFrame.

```python
def consolidate(
    files: list[str] = None,
    output_filename: str = None,
    subdir: str = 'daily',
    save: bool = True,
    verbose: bool = False,
    add_source: bool = False,
) -> pd.DataFrame
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| files | list | None | Arquivos a consolidar (default: todos) |
| output_filename | str | None | Nome do arquivo consolidado |
| subdir | str | 'daily' | Subdiretorio fonte |
| save | bool | True | Salvar em processed/ |
| add_source | bool | False | Adicionar coluna '_source' |

**Comportamento:**
- `add_source=False`: Join horizontal por indice. Renomeia coluna 'value' para nome do arquivo.
- `add_source=True`: Concat vertical. Adiciona coluna '_source' com nome do arquivo origem.

```python
# Join horizontal (series temporais)
df = dm.consolidate(
    subdir='bacen/sgs/daily',
    output_filename='sgs_daily_consolidated'
)
# Resultado: colunas [selic, cdi, dolar_ptax, ...]

# Concat vertical (expectativas)
df = dm.consolidate(
    subdir='bacen/expectations',
    output_filename='expectations_consolidated',
    add_source=True
)
# Resultado: todas as linhas + coluna _source
```

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
│   └── ipea/
│       └── monthly/         # caged_saldo.parquet, ...
└── processed/               # Dados consolidados
    ├── bacen_sgs_daily_consolidated.parquet
    ├── bacen_sgs_monthly_consolidated.parquet
    ├── expectations_consolidated.parquet
    └── ipea_monthly_consolidated.parquet
```

---

## Formato de Dados

### Parquet

- **Engine:** PyArrow
- **Compressao:** Snappy
- **Indice:** Preservado (DatetimeIndex)

### Convencoes

- **Indice:** DatetimeIndex para series temporais
- **Coluna de valor:** `value` (normalizado pelos clients)
- **Metadata:** Armazenada em `df.attrs`

```python
df.attrs = {
    'filename': 'selic',
    'subdir': 'bacen/sgs/daily',
    'saved_at': '2024-12-06T10:30:00',
    'last_update': '2024-12-06T15:00:00',
    # ... metadata adicional
}
```

---

## Metodos de Compatibilidade

Wrappers para API antiga (uso desencorajado):

| Metodo Antigo | Equivalente Novo |
|---------------|------------------|
| `save_indicator(df, key, freq)` | `save(df, filename=key, subdir=freq)` |
| `read_indicator(key, freq)` | `read(filename=key, subdir=freq)` |
| `append_indicator(df, key, freq)` | `append(df, filename=key, subdir=freq)` |
| `list_indicators(freq)` | `list_files(subdir=freq)` |
| `consolidate_daily()` | `consolidate(subdir='daily')` |
| `consolidate_monthly()` | `consolidate(subdir='monthly')` |

---

## Import

```python
from src.core.data import DataManager
```
