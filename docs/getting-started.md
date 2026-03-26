# Getting Started

Guia rapido para comecar a usar o `adb`.

## Instalacao

```bash
uv add adb --git https://github.com/seu-usuario/adb.git
```

## Primeiro Uso

```python
import adb

# Fetch direto da API (stateless, sem disco)
df = adb.sgs.fetch('selic', start='2020')
print(df.head())
```

## Modos de Uso

### fetch() -- stateless (recomendado para explorar)

Busca dados direto da API. Nao salva nada em disco.

```python
df = adb.sgs.fetch('selic', start='2020')
df = adb.sgs.fetch('selic', 'cdi', start='2024')   # Multiplos indicadores
df = adb.ipea.fetch('caged_saldo', start='2024')
df = adb.sidra.fetch('ipca', start='2024')
```

### collect() + read() -- com cache local

Para uso recorrente. Coleta uma vez, le varias vezes.

```python
# Coletar (incremental -- so baixa dados novos)
adb.sgs.collect()
adb.sgs.collect('selic', start='2020', end='2024')  # Range especifico

# Ler do cache
df = adb.sgs.read('selic', start='2020')
df = adb.sgs.read('selic', 'cdi', 'dolar_ptax')     # Join automatico por data
```

## Metodos Disponiveis

Todos os explorers compartilham a mesma interface:

| Metodo | Descricao |
|--------|-----------|
| `.fetch(*indicators, start, end)` | Busca direto da API (stateless) |
| `.read(*indicators, start, end)` | Le dados salvos localmente |
| `.collect(indicators, start, end)` | Baixa dados e salva em Parquet |
| `.available(**filters)` | Lista indicadores disponiveis |
| `.info(indicator)` | Retorna metadados do indicador |
| `.status()` | Mostra status/saude dos arquivos salvos |

## Fontes de Dados

| Fonte | Explorer | Dados |
|-------|----------|-------|
| BCB SGS | `adb.sgs` | Series temporais (Selic, CDI, PTAX, IBC-Br, IGP-M) |
| BCB Focus | `adb.expectations` | Expectativas de mercado (IPCA, PIB, Cambio) |
| IBGE SIDRA | `adb.sidra` | Dados economicos (IPCA, PIB, PNAD) |
| IPEA | `adb.ipea` | Series agregadas IPEADATA |
| Bloomberg | `adb.bloomberg` | Dados de mercado (requer terminal) |

## Exemplos

### Indicadores disponiveis

```python
adb.sgs.available()
# ['ibc_br_bruto', 'ibc_br_dessaz', 'igp_m', 'selic', 'cdi', ...]

adb.sgs.available(frequency='daily')
# ['selic', 'dolar_ptax', 'euro_ptax', 'cdi']

adb.sgs.info('selic')
# {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily', ...}
```

### Status dos dados

```python
adb.sgs.status()
# Retorna DataFrame com: arquivo, subdir, registros, primeira_data,
# ultima_data, cobertura, gaps, status (OK/STALE/NOT_COLLECTED)
```

### Expectations (Focus)

```python
# Dados brutos
df = adb.expectations.fetch('ipca_anual', start='2024')

# Serie processada (Selic esperada para fim de 2026)
df = adb.expectations.fetch('selic_anual', start='2024', year=2026)

# IPCA 12 meses suavizado
df = adb.expectations.fetch('ipca_12m', start='2024', smooth=True)
```

## Proximos Passos

- Documentacao de cada [provider](providers/) para opcoes especificas
- [Queries SQL avancadas](advanced/querying.md) com DuckDB
- [Como adicionar providers](advanced/extending.md)
