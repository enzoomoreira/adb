# agora-database

Coleta, armazenamento e visualizacao de dados economicos brasileiros. Suporta seis fontes de dados com interface unificada.

| Fonte | Modulo | Dados |
|-------|--------|-------|
| BCB - SGS | `adb.sgs` | Series temporais (Selic, CDI, IPCA, cambio) |
| BCB - Focus | `adb.expectations` | Expectativas de mercado |
| IBGE - SIDRA | `adb.sidra` | Dados demograficos e economicos (IPCA, PIB) |
| IPEA | `adb.ipea` | Dados agregados de emprego |
| MTE - CAGED | `adb.caged` | Microdados de emprego formal |
| Bloomberg | `adb.bloomberg` | Dados de mercado financeiro (Terminal) |

## Instalacao

```bash
uv sync
```

## Uso Rapido

```python
import adb

# Leitura de dados
df = adb.sgs.read('selic', start='2020')
df = adb.sgs.read('selic', 'cdi')           # Multiplos indicadores
df = adb.expectations.read('ipca_anual')
df = adb.sidra.read('ipca')
df = adb.caged.read(year=2024, month=10)

# Indicadores disponiveis
adb.sgs.available()
adb.sgs.info('selic')

# Coleta de dados
adb.sgs.collect()
adb.sgs.collect(['selic', 'cdi'])

# Status dos dados salvos
adb.sgs.get_status()
```

## Documentacao

### Guias de Uso

- **[getting-started.md](docs2/getting-started.md)** - Instalacao e primeiro uso

### Fontes de Dados

- **[bacen.md](docs2/providers/bacen.md)** - BCB (SGS + Expectations)
- **[ibge.md](docs2/providers/ibge.md)** - IBGE/SIDRA
- **[ipea.md](docs2/providers/ipea.md)** - IPEA
- **[mte.md](docs2/providers/mte.md)** - MTE/CAGED
- **[bloomberg.md](docs2/providers/bloomberg.md)** - Bloomberg Terminal

### Uso Avancado

- **[querying.md](docs2/advanced/querying.md)** - Queries SQL com DuckDB
- **[extending.md](docs2/advanced/extending.md)** - Como adicionar novos providers

### Arquitetura Interna

- **[architecture.md](docs2/internals/architecture.md)** - Visao geral da arquitetura
- **[domain.md](docs2/internals/domain.md)** - BaseExplorer, Schemas, Exceptions
- **[infra.md](docs2/internals/infra.md)** - Config, Logging, Persistencia
- **[services.md](docs2/internals/services.md)** - BaseCollector, Registry

## Estrutura de Dados

```
data/raw/
  bacen/
    sgs/
      daily/          # selic.parquet, cdi.parquet, dolar_ptax.parquet...
      monthly/        # ibc_br_bruto.parquet, igp_m.parquet...
    expectations/     # ipca_anual.parquet, selic_anual.parquet...
  ibge/
    sidra/
      monthly/        # ipca.parquet, ipca_12m.parquet...
  ipea/
    monthly/          # caged_saldo.parquet, taxa_desemprego.parquet...
  mte/
    caged/            # cagedmov_2024-01.parquet...
  bloomberg/
    daily/            # ibov_points.parquet, brent.parquet...
```

## Visualizacao (chartkit)

A visualizacao de graficos e feita pela biblioteca externa **chartkit**.

```python
import chartkit

df.chartkit.plot(title="Selic", kind='line', units='%')
```
