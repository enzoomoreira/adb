# adb

Acesso unificado a dados economicos brasileiros. Agrega multiplas fontes sob uma API consistente com normalizacao e validacao de qualidade.

| Fonte | Modulo | Dados |
|-------|--------|-------|
| BCB - SGS | `adb.sgs` | Series temporais (Selic, CDI, PTAX, IBC-Br, IGP-M) |
| BCB - Focus | `adb.expectations` | Expectativas de mercado |
| IBGE - SIDRA | `adb.sidra` | Dados demograficos e economicos (IPCA, PIB) |
| IPEA | `adb.ipea` | Dados agregados IPEADATA |
| Bloomberg | `adb.bloomberg` | Dados de mercado financeiro (Terminal) |

## Instalacao

```bash
uv add adb --git https://github.com/seu-usuario/adb.git
```

## Uso Rapido

```python
import adb

# Fetch direto da API (stateless, sem disco)
df = adb.sgs.fetch('selic', start='2020')
df = adb.sgs.fetch('selic', 'cdi')          # Multiplos indicadores

# Cache local (coleta + leitura de disco)
adb.sgs.collect()                              # incremental
adb.sgs.collect('selic', start='2020', end='2024')  # range especifico
df = adb.sgs.read('selic', start='2020')

# Indicadores disponiveis
adb.sgs.available()
adb.sgs.info('selic')

# Status dos dados salvos
adb.sgs.status()
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
- **[bloomberg.md](docs/providers/bloomberg.md)** - Bloomberg Terminal

### Uso Avancado

- **[querying.md](docs/advanced/querying.md)** - Queries SQL com DuckDB
- **[extending.md](docs/advanced/extending.md)** - Como adicionar novos providers

### Arquitetura Interna

- **[architecture.md](docs/internals/architecture.md)** - Estrutura, fluxos e padroes de projeto
