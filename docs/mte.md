# Modulo MTE (Ministerio do Trabalho e Emprego)

Documentacao do coletor de microdados do Novo CAGED.

## Visao Geral

O modulo `src/adb/mte/` coleta microdados de emprego formal via FTP do MTE.

| Caracteristica | Valor |
|----------------|-------|
| Fonte | FTP ftp.mtps.gov.br |
| Formato origem | 7z -> CSV -> Parquet |
| Periodo | 2020-presente (Novo CAGED) |
| Volume | ~500MB-1GB por mes |
| Atualizacao | Mensal (~2 meses de atraso) |

---

## Uso Basico

### Coleta de Dados

```python
import adb

adb.caged.collect()                              # Todos indicadores, todos periodos
adb.caged.collect(indicators='cagedmov')         # Um indicador
adb.caged.collect(indicators=['cagedmov', 'cagedfor'])  # Lista de indicadores
adb.caged.collect(max_workers=8)                 # Ajustar paralelismo
```

### Leitura de Microdados

```python
import adb

# Leitura basica (year obrigatorio)
df = adb.caged.read(year=2024)                   # Ano inteiro (todos os meses)
df = adb.caged.read(year=2024, month=6)          # Mes especifico
df = adb.caged.read(year=2024, uf=35)            # Filtrado por UF (35=SP)
df = adb.caged.read(year=2024, dataset='cagedfor')  # Outro dataset

# Parametros adicionais
df = adb.caged.read(year=2024, columns=['uf', 'saldomovimentacao'])
df = adb.caged.read(year=2024, where="saldomovimentacao > 0")
```

### Consultas Agregadas

```python
import adb

# Agregacoes pre-definidas (year obrigatorio)
df = adb.caged.saldo_mensal(year=2024)           # Saldo por mes
df = adb.caged.saldo_por_uf(year=2024)           # Saldo por UF
df = adb.caged.saldo_por_setor(year=2024)        # Saldo por setor (CNAE)

# Com filtros
df = adb.caged.saldo_mensal(year=2024, uf=35)    # Saldo mensal de SP
df = adb.caged.saldo_por_setor(year=2024, month=6, uf=33)  # Setor, Jun/2024, RJ
```

### Informacoes e Status

```python
import adb

# Periodos disponiveis (arquivos salvos)
periodos = adb.caged.available_periods()          # [(2020, 1), (2020, 2), ...]
periodos = adb.caged.available_periods('cagedfor')

# Status dos dados
status = adb.caged.get_status()                   # DataFrame com metadados
# Colunas: arquivo, subdir, registros, colunas, primeira_data, ultima_data, status
```

---

## Queries SQL Diretas

Para queries customizadas, use o QueryEngine:

```python
from adb.core.data import QueryEngine

qe = QueryEngine()

# Leitura com filtros via glob
df = qe.read_glob('cagedmov_2024-*.parquet', subdir='mte/caged')
df = qe.read_glob('cagedmov_*.parquet', subdir='mte/caged',
                  columns=['uf', 'saldomovimentacao'],
                  where="uf = 35")

# Query SQL com DuckDB
df = qe.sql('''
    SELECT uf, SUM(saldomovimentacao) as saldo
    FROM '{raw}/mte/caged/cagedmov_*.parquet'
    WHERE competenciamov >= 202401
    GROUP BY uf
    ORDER BY saldo DESC
''')
```

Veja [core.md](core.md) para documentacao completa do QueryEngine.

---

## CAGED_CONFIG

Indicadores disponiveis em `src/adb/mte/caged/indicators.py`:

| Chave | Prefixo FTP | Descricao | Inicio |
|-------|-------------|-----------|--------|
| cagedmov | CAGEDMOV | Movimentacoes (admissoes e desligamentos) | 2020 |
| cagedfor | CAGEDFOR | Declaracoes fora do prazo | 2020 |
| cagedexc | CAGEDEXC | Exclusoes de movimentacoes | 2020 |

### Informacoes dos Indicadores

```python
import adb

# Listar indicadores disponiveis
adb.caged.info()
# {'cagedmov': {...}, 'cagedfor': {...}, 'cagedexc': {...}}

# Detalhes de um indicador
adb.caged.info('cagedmov')
# {
#     "prefix": "CAGEDMOV",
#     "name": "Movimentacoes",
#     "description": "Movimentacoes CAGED (admissoes e desligamentos)",
#     "start_year": 2020,
# }
```

---

## Uso Avancado (Acesso Direto)

Para casos especiais que requerem controle fino:

### Collector

```python
from adb.mte.caged.collector import CAGEDCollector

collector = CAGEDCollector()
collector.collect('cagedmov', max_workers=4)
collector.collect(['cagedmov', 'cagedfor'], verbose=False)

# Status dos arquivos
status = collector.get_status()
```

### Client (FTP)

```python
from adb.mte.caged.client import CAGEDClient

client = CAGEDClient(timeout=300)
client.connect()

# Download de arquivo especifico
file_path = client.download_to_file(prefix='CAGEDMOV', year=2024, month=10)

# Listar arquivos disponiveis
files = client.list_files()              # Todos
files = client.list_files(year=2024)     # Ano especifico

client.disconnect()
```

### Explorer

```python
from adb.mte.caged.explorer import CAGEDExplorer

explorer = CAGEDExplorer()
df = explorer.read(year=2024, month=6)
df = explorer.saldo_por_uf(year=2024)
```

---

## API Reference

### CAGEDExplorer

```python
class CAGEDExplorer(BaseExplorer):
    """Explorer para microdados CAGED."""

    def read(
        self,
        year: int,
        month: int = None,
        dataset: str = "cagedmov",
        uf: int = None,
        columns: list[str] = None,
        where: str = None,
    ) -> pd.DataFrame:
        """Le microdados CAGED."""

    def saldo_por_uf(
        self,
        year: int,
        month: int = None,
        dataset: str = "cagedmov",
    ) -> pd.DataFrame:
        """Calcula saldo de empregos por UF. Retorna: uf, saldo, registros"""

    def saldo_mensal(
        self,
        year: int,
        uf: int = None,
        dataset: str = "cagedmov",
    ) -> pd.DataFrame:
        """Calcula saldo de empregos mensal. Retorna: ano, mes, saldo, registros"""

    def saldo_por_setor(
        self,
        year: int,
        month: int = None,
        uf: int = None,
        dataset: str = "cagedmov",
    ) -> pd.DataFrame:
        """Calcula saldo por setor economico (secao CNAE). Retorna: setor, saldo, registros"""

    def available_periods(self, dataset: str = "cagedmov") -> list[tuple]:
        """Retorna periodos (ano, mes) disponiveis nos arquivos salvos."""

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        max_workers: int = 4,
    ) -> None:
        """Dispara coleta delegando ao CAGEDCollector."""

    def get_status(self) -> pd.DataFrame:
        """Retorna status dos arquivos salvos por indicador."""
```

### CAGEDCollector

```python
class CAGEDCollector(BaseCollector):
    """Orquestra coleta de dados do Novo CAGED."""

    default_subdir = 'mte/caged'

    def __init__(self, data_path: Path = None):
        """Inicializa collector com path opcional."""

    def collect(
        self,
        indicators: list[str] | str = "all",
        save: bool = True,
        verbose: bool = True,
        max_workers: int = 4,
    ) -> None:
        """
        Coleta dados do CAGED (Raw Layer).

        - Download paralelo via ThreadPoolExecutor
        - Conversao 7z -> CSV -> Parquet via DuckDB
        - Atualizacao incremental (apenas meses faltantes)
        """

    def get_status(self) -> pd.DataFrame:
        """Retorna status agregado dos arquivos por indicador."""
```

### CAGEDClient

```python
class CAGEDClient:
    """Cliente FTP para download de microdados do Novo CAGED."""

    FTP_HOST = "ftp.mtps.gov.br"
    BASE_PATH = "/pdet/microdados/NOVO CAGED"

    def __init__(self, timeout: int = 300):
        """Inicializa cliente FTP."""

    def connect(self) -> FTP:
        """Conecta ao servidor FTP (anonimo). Retry automatico."""

    def disconnect(self):
        """Fecha conexao FTP."""

    def download_to_file(
        self,
        prefix: str,
        year: int,
        month: int,
        target_path: Path | str = None,
    ) -> Path:
        """Download de arquivo 7z. Retorna path do arquivo baixado."""

    def list_files(self, year: int = None) -> list[str]:
        """Lista arquivos disponiveis no FTP."""
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

**Convencao de nomes:** `{indicador}_{ano}-{mes:02d}.parquet`

**Estrategia de armazenamento:**
- Arquivos mensais individuais para baixo uso de memoria
- Atualizacao incremental simples (apenas baixa meses faltantes)
- Query eficiente com DuckDB via glob patterns

---

## Processamento de Dados

Durante a coleta, o collector realiza:

1. **Download**: Arquivo `.7z` via FTP
2. **Extracao**: Descompactacao com py7zr
3. **Limpeza de dados** (via DuckDB):
   - Converte colunas numericas de formato brasileiro (virgula -> ponto)
   - Renomeia colunas removendo acentos (`salário` -> `salario`)
   - CSV delimiter: ponto-e-virgula (`;`)
   - Encoding: UTF-8 (com ignore_errors)
4. **Persistencia**: Salva como Parquet com Snappy compression

---

## Notas Importantes

1. **Volume de dados**: CAGED tem milhoes de registros por mes. Use filtros (`uf`, `columns`, `where`) para evitar carregar tudo na memoria.

2. **Coluna de competencia**: `competenciamov` no formato YYYYMM (inteiro). Para filtros SQL, use valores como `202401`.

3. **UF codes**: Use codigos IBGE (35=SP, 33=RJ, 31=MG, etc).

4. **Paralelismo**: O parametro `max_workers` controla threads de download. Valores maiores aceleram a coleta inicial mas aumentam uso de banda.

5. **Resiliencia**: Client FTP tem retry automatico com backoff exponencial para lidar com instabilidades de rede.
