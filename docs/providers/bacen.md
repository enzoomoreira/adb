# Banco Central do Brasil (BCB)

O modulo BCB oferece acesso a dados publicos do Banco Central atraves de dois explorers:

| Explorer | Fonte | Descricao |
|----------|-------|-----------|
| `adb.sgs` | API SGS | Series temporais (Selic, CDI, IPCA, cambio, IBC-Br) |
| `adb.expectations` | API Focus | Expectativas de mercado (relatorio Focus) |

---

## SGS - Series Temporais

O Sistema Gerenciador de Series (SGS) disponibiliza series historicas de indicadores economicos.

### Indicadores Disponiveis

**Diarios:**

| Chave | Codigo | Nome | Descricao |
|-------|--------|------|-----------|
| `selic` | 432 | Meta Selic | Taxa basica de juros da economia brasileira |
| `selic_acum_mensal` | 4390 | Selic Acumulada no Mes | Taxa de juros acumulada no mes |
| `cdi` | 12 | CDI | Certificado de Deposito Interbancario |
| `dolar_ptax` | 10813 | Dolar PTAX | Taxa de cambio Dolar/Real - PTAX Venda |
| `euro_ptax` | 21619 | Euro PTAX | Taxa de cambio Euro/Real - PTAX Venda |

**Mensais:**

| Chave | Codigo | Nome | Descricao |
|-------|--------|------|-----------|
| `ibc_br_bruto` | 24363 | IBC-Br Bruto | Indice de Atividade Economica - Bruto |
| `ibc_br_dessaz` | 24364 | IBC-Br Dessazonalizado | Indice de Atividade Economica - Dessazonalizado |
| `igp_m` | 189 | IGP-M | Indice Geral de Precos do Mercado |
| `ibc_br_agro` | 29602 | IBC-Br Agropecuaria | IBC-Br Setor Agropecuario - Dessazonalizado |
| `ibc_br_industria` | 29604 | IBC-Br Industria | IBC-Br Setor Industrial - Dessazonalizado |
| `ibc_br_servicos` | 29606 | IBC-Br Servicos | IBC-Br Setor de Servicos - Dessazonalizado |

### Uso

```python
import adb

# Listar indicadores disponiveis
adb.sgs.available()
# ['selic', 'selic_acum_mensal', 'cdi', 'dolar_ptax', 'euro_ptax', ...]

# Informacoes de um indicador
adb.sgs.info('selic')
# IndicatorConfig(code=432, name='Meta Selic', frequency='daily', ...)

# Coletar dados
adb.sgs.collect()                      # Todos indicadores
adb.sgs.collect('selic')               # Um indicador
adb.sgs.collect(['selic', 'cdi'])      # Lista de indicadores

# Ler dados
df = adb.sgs.read('selic')
df = adb.sgs.read('selic', start='2020')
df = adb.sgs.read('selic', start='2020', end='2023')
df = adb.sgs.read('selic', 'cdi')      # Multiplos indicadores

# Status dos arquivos locais
adb.sgs.status()
```

---

## Expectations - Relatorio Focus

O relatorio Focus consolida as expectativas do mercado financeiro para indicadores macroeconomicos.

### Indicadores Disponiveis

**Anuais (Top 5 previsores):**

| Chave | Indicador | Descricao |
|-------|-----------|-----------|
| `ipca_anual` | IPCA | Expectativa IPCA anual |
| `igpm_anual` | IGP-M | Expectativa IGP-M anual |
| `pib_anual` | PIB Total | Expectativa PIB anual |
| `cambio_anual` | Cambio | Expectativa Cambio fim de ano |
| `selic_anual` | Selic | Expectativa Selic fim de ano |

**Mensais:**

| Chave | Indicador | Descricao |
|-------|-----------|-----------|
| `ipca_mensal` | IPCA | Expectativa IPCA mensal |
| `igpm_mensal` | IGP-M | Expectativa IGP-M mensal |
| `cambio_mensal` | Cambio | Expectativa Cambio mensal |

**Selic e Inflacao:**

| Chave | Indicador | Descricao |
|-------|-----------|-----------|
| `selic` | Selic | Expectativa Selic por reuniao COPOM |
| `ipca_12m` | IPCA | Expectativa IPCA acumulado 12 meses |
| `ipca_24m` | IPCA | Expectativa IPCA acumulado 24 meses |
| `igpm_12m` | IGP-M | Expectativa IGP-M acumulado 12 meses |

### Uso

```python
import adb

# Listar indicadores disponiveis
adb.expectations.available()

# Informacoes de um indicador
adb.expectations.info('ipca_anual')

# Coletar dados
adb.expectations.collect()
adb.expectations.collect('ipca_anual')

# Ler dados
df = adb.expectations.read('ipca_anual')
df = adb.expectations.read('ipca_anual', start='2024')
```

### Parametros Especiais

O explorer de Expectations oferece parametros adicionais para filtrar os dados:

```python
# Filtrar por ano de referencia
df = adb.expectations.read('selic_anual', year=2027)

# Filtrar por serie suavizada
df = adb.expectations.read('ipca_12m', smooth=True)
df = adb.expectations.read('ipca_12m', smooth=False)

# Escolher metrica (default: 'Mediana')
df = adb.expectations.read('ipca_12m', smooth=True, metric='Media')
df = adb.expectations.read('ipca_12m', smooth=True, metric='Minimo')
df = adb.expectations.read('ipca_12m', smooth=True, metric='Maximo')
```

**Parametros disponiveis:**

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `year` | `int` | Filtra por ano de referencia |
| `smooth` | `bool` | Filtra por serie suavizada (`True` = suavizada, `False` = nao suavizada) |
| `metric` | `str` | Metrica a retornar: `'Mediana'`, `'Media'`, `'Minimo'`, `'Maximo'` |

---

## Arquivos Gerados

Apos a coleta, os dados sao salvos em formato Parquet:

```
data/bacen/
├── sgs/
│   ├── daily/
│   │   ├── selic.parquet
│   │   ├── cdi.parquet
│   │   ├── dolar_ptax.parquet
│   │   └── euro_ptax.parquet
│   └── monthly/
│       ├── ibc_br_bruto.parquet
│       ├── ibc_br_dessaz.parquet
│       ├── igp_m.parquet
│       └── ...
└── expectations/
    ├── ipca_anual.parquet
    ├── selic.parquet
    ├── ipca_12m.parquet
    └── ...
```
