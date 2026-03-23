# adb

Coleta e consulta de dados economicos de multiplas fontes. Interface unificada para series temporais e microdados.

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
uv add adb --git https://github.com/seu-usuario/adb.git
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

## Configuracao

Dados sao armazenados no cache do OS via `platformdirs`:

| OS | Path |
|----|------|
| Windows | `%LOCALAPPDATA%/py-adb/Cache` |
| Linux | `~/.cache/py-adb` |
| macOS | `~/Library/Caches/py-adb` |

Override via variavel de ambiente:

```bash
export ADB_DATA_DIR=/caminho/customizado
```

## Documentacao

### Guias de Uso

- **[getting-started.md](docs/getting-started.md)** - Instalacao e primeiro uso

### Fontes de Dados

- **[bacen.md](docs/providers/bacen.md)** - BCB (SGS + Expectations)
- **[ibge.md](docs/providers/ibge.md)** - IBGE/SIDRA
- **[ipea.md](docs/providers/ipea.md)** - IPEA
- **[mte.md](docs/providers/mte.md)** - MTE/CAGED
- **[bloomberg.md](docs/providers/bloomberg.md)** - Bloomberg Terminal

### Uso Avancado

- **[querying.md](docs/advanced/querying.md)** - Queries SQL com DuckDB
- **[extending.md](docs/advanced/extending.md)** - Como adicionar novos providers

### Arquitetura Interna

- **[architecture.md](docs/internals/architecture.md)** - Visao geral da arquitetura
- **[domain.md](docs/internals/domain.md)** - BaseExplorer, Schemas, Exceptions
- **[infra.md](docs/internals/infra.md)** - Config, Logging, Persistencia
- **[services.md](docs/internals/services.md)** - BaseCollector, Registry
