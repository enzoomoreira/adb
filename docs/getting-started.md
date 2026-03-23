# Getting Started

Guia rapido para comecar a usar o `adb`.

## Instalacao

Instale como dependencia no seu projeto:

```bash
uv add adb --git https://github.com/seu-usuario/adb.git
```

## Primeiro Uso

```python
import adb

# Coletar dados da Selic (apenas na primeira vez)
adb.sgs.collect(indicators=['selic'])

# Ler os dados
df = adb.sgs.read('selic', start='2020')
print(df.head())
```

## Padrao de Uso

O fluxo de trabalho segue 3 etapas:

### 1. Coleta

Baixa dados da fonte e salva localmente em Parquet:

```python
# Coletar todos os indicadores de uma fonte
adb.sgs.collect()

# Coletar indicadores especificos
adb.sgs.collect(indicators=['selic', 'cdi'])
```

### 2. Leitura

Le os dados salvos localmente:

```python
# Ler um indicador
df = adb.sgs.read('selic')

# Ler multiplos indicadores (join automatico por data)
df = adb.sgs.read('selic', 'cdi', 'dolar_ptax')

# Filtrar por periodo
df = adb.sgs.read('selic', start='2020', end='2023')
df = adb.sgs.read('selic', start='2020-06')  # A partir de junho/2020
```

## Metodos Disponiveis

Todos os explorers compartilham a mesma interface:

| Metodo | Descricao |
|--------|-----------|
| `.read(*indicators, start, end)` | Le dados salvos localmente |
| `.collect(indicators, **kwargs)` | Baixa dados da fonte |
| `.available()` | Lista indicadores disponiveis |
| `.info(indicator)` | Retorna metadados do indicador |
| `.get_status()` | Mostra status dos arquivos salvos |

## Fontes de Dados

| Fonte | Explorer | Descricao | Documentacao |
|-------|----------|-----------|--------------|
| BCB SGS | `adb.sgs` | Series temporais BCB (Selic, CDI, PTAX, IBC-Br) | [providers/sgs.md](providers/sgs.md) |
| BCB Expectations | `adb.expectations` | Expectativas Focus (IPCA, PIB, Cambio) | [providers/expectations.md](providers/expectations.md) |
| IBGE SIDRA | `adb.sidra` | Tabelas IBGE (IPCA, PIB, PNAD) | [providers/sidra.md](providers/sidra.md) |
| IPEA | `adb.ipea` | Series IPEADATA | [providers/ipea.md](providers/ipea.md) |
| MTE CAGED | `adb.caged` | Microdados de emprego formal | [providers/caged.md](providers/caged.md) |
| Bloomberg | `adb.bloomberg` | Dados de mercado (requer terminal) | [providers/bloomberg.md](providers/bloomberg.md) |

## Exemplos Rapidos

### Consultar indicadores disponiveis

```python
# Listar todos os indicadores de uma fonte
print(adb.sgs.available())
# ['ibc_br_bruto', 'ibc_br_dessaz', 'igp_m', 'selic', 'cdi', ...]

# Filtrar por atributo
print(adb.sgs.available(frequency='daily'))
# ['selic', 'dolar_ptax', 'euro_ptax', 'cdi']
```

### Obter informacoes de um indicador

```python
info = adb.sgs.info('selic')
print(info)
# {'code': 432, 'name': 'Meta Selic', 'frequency': 'daily', ...}
```

### Verificar status dos dados

```python
status = adb.sgs.get_status()
print(status)
#            indicator  last_update  rows
# 0              selic   2025-01-15  5420
# 1                cdi   2025-01-15  6230
```

### CAGED - Microdados

```python
# Coletar dados de um ano
adb.caged.collect(year=2024)

# Ler filtrando por UF (35 = SP)
df = adb.caged.read(year=2024, uf=35)
```

### Expectativas Focus

```python
# Coletar expectativas
adb.expectations.collect()

# Ler projecoes de IPCA
df = adb.expectations.read('ipca', start='2024')
```

## Proximos Passos

- Consulte a documentacao de cada [provider](providers/) para opcoes especificas
- Veja [advanced/](advanced/) para uso avancado e customizacao
