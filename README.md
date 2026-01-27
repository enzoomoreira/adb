# agora-database

Coleta, armazenamento e visualizacao de dados economicos brasileiros. Suporta seis fontes de dados com interface unificada.

| Fonte | Modulo | Dados | Docs |
|-------|--------|-------|------|
| BCB - SGS | `adb.sgs` | Series temporais (Selic, CDI, IPCA, cambio) | [bacen.md](docs/bacen.md) |
| BCB - Focus | `adb.expectations` | Expectativas de mercado | [bacen.md](docs/bacen.md) |
| IBGE - SIDRA | `adb.sidra` | Dados demograficos e economicos (IPCA, PIB) | [ibge.md](docs/ibge.md) |
| IPEA | `adb.ipea` | Dados agregados de emprego | [ipea.md](docs/ipea.md) |
| MTE - CAGED | `adb.caged` | Microdados de emprego formal | [mte.md](docs/mte.md) |
| Bloomberg | `adb.bloomberg` | Dados de mercado financeiro (Terminal) | [bloomberg.md](docs/bloomberg.md) |

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

## Documentacao

- **[architecture.md](docs/architecture.md)** - Visao geral da arquitetura, componentes e fluxos
- **[core.md](docs/core.md)** - Modulo central (QueryEngine, DataManager, Explorers, utils)
- **[charting.md](docs/charting.md)** - Visualizacao com `.agora.plot()`
- **[bacen.md](docs/bacen.md)** - SGS e Expectations (Banco Central)
- **[ibge.md](docs/ibge.md)** - SIDRA (IBGE)
- **[ipea.md](docs/ipea.md)** - Dados agregados IPEA
- **[mte.md](docs/mte.md)** - CAGED (microdados de emprego)
- **[bloomberg.md](docs/bloomberg.md)** - Dados de mercado financeiro
