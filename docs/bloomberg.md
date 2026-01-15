# Modulo Bloomberg Terminal

Documentacao do coletor de dados do Bloomberg Terminal.

## Visao Geral

O modulo `src/bloomberg/` coleta dados de mercado financeiro via Bloomberg Terminal.

| Caracteristica | Valor |
|----------------|-------|
| Fonte | Bloomberg Terminal (xbbg) |
| Formato | Series temporais |
| Foco | Dados de mercado financeiro (commodities, indices, cambio) |
| Requisito | Bloomberg Terminal ativo |

**Por que usar Bloomberg?**
- Acesso a dados premium de mercado financeiro
- Dados atualizados em tempo real
- Ampla cobertura de ativos financeiros globais

---

## BloombergCollector

Orquestra a coleta de series temporais do Bloomberg Terminal.

### Uso Basico

```python
from src.bloomberg import BloombergCollector

collector = BloombergCollector(data_path='data/')

# Coleta de indicadores
results = collector.collect('bz1_comdty')                  # Um ticker
results = collector.collect(['bz1_comdty', 'cl1_comdty'])  # Lista
results = collector.collect()                              # Todos (default='all')

# Consolidacao
df = collector.consolidate()

# Status
collector.get_status()
```

### Metodos

#### collect(indicators='all', save=True, verbose=True)

Coleta um ou mais tickers da configuracao predefinida.

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| indicators | str\|list | 'all', lista ou string unica |
| save | bool | Salvar em Parquet |
| verbose | bool | Imprimir progresso |

**Retorno:** dict[str, DataFrame]

#### consolidate(subdir='bloomberg/daily', output_filename='bloomberg_daily_consolidated', save=True, verbose=True)

Consolida arquivos de um subdiretorio via join horizontal por indice (data).

**Retorno:** DataFrame consolidado

#### get_status(subdir='bloomberg/daily')

Retorna status dos arquivos salvos (registros, datas, status).

**Retorno:** DataFrame

---

## BLOOMBERG_CONFIG

Indicadores disponiveis em `src/bloomberg/indicators.py`:

### Commodities

| Chave | Ticker | Nome | Lookback |
|-------|--------|------|----------|
| bz1_comdty | BZ1 Comdty | Brent Crude Oil (Front Month) | 730 dias |
| cl1_comdty | CL1 Comdty | WTI Crude Oil (Front Month) | 730 dias |
| gc1_comdty | GC1 Comdty | Gold (Front Month) | 730 dias |

### Indices

| Chave | Ticker | Nome | Lookback |
|-------|--------|------|----------|
| spx_index | SPX Index | S&P 500 Index | 730 dias |
| ibov_index | IBOV Index | Ibovespa Index | 730 dias |

### Cambio

| Chave | Ticker | Nome | Lookback |
|-------|--------|------|----------|
| usdbrl_curncy | USDBRL Curncy | USD/BRL Spot | 730 dias |

**Nota:** Lookback configuravel permite ajustar o periodo de coleta inicial por ticker.

---

## BloombergClient

Cliente de baixo nivel para acesso ao Bloomberg Terminal (wrapper do xbbg).

```python
from src.bloomberg import BloombergClient

client = BloombergClient()

# Busca serie temporal
df = client.get_data(ticker='BZ1 Comdty', lookback_days=365)

# Com periodo especifico
df = client.get_data(
    ticker='BZ1 Comdty',
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

**Normalizacao:**
- Saida padronizada: DatetimeIndex (sem timezone) + coluna 'value'
- Compativel com o padrao do projeto (igual ao SGS/IPEA)

**Campos retornados:**
- `value`: Preco de fechamento (PX_LAST)
- Outros campos podem ser configurados no client

---

## Funcoes Auxiliares

**Nota:** As funcoes auxiliares agora sao fornecidas pelo modulo centralizado `core.indicators`.

```python
from src.bloomberg import BLOOMBERG_CONFIG
from core.indicators import list_indicators, get_indicator_config, filter_by_field

list_indicators(BLOOMBERG_CONFIG)                   # Lista chaves disponiveis
get_indicator_config(BLOOMBERG_CONFIG, 'bz1_comdty') # Retorna config completa
filter_by_field(BLOOMBERG_CONFIG, 'lookback_days', 730)  # Filtra por lookback
```

---

## Imports Publicos

```python
from src.bloomberg import (
    # Collector
    BloombergCollector,

    # Client
    BloombergClient,

    # Configuracoes
    BLOOMBERG_CONFIG,
)

# Funcoes auxiliares (centralizadas em core.indicators)
from core.indicators import (
    list_indicators,
    get_indicator_config,
    filter_by_field,
)
```

---

## Arquivos Gerados

```
data/
├── raw/
│   └── bloomberg/
│       └── daily/
│           ├── bz1_comdty.parquet
│           ├── cl1_comdty.parquet
│           ├── gc1_comdty.parquet
│           ├── spx_index.parquet
│           ├── ibov_index.parquet
│           └── usdbrl_curncy.parquet
└── processed/
    └── bloomberg_daily_consolidated.parquet
```

---

## Extensibilidade

Para adicionar novos tickers Bloomberg:

```python
# Em src/bloomberg/indicators.py
BLOOMBERG_CONFIG['novo_ticker'] = {
    'ticker': 'TICKER Bloomberg',      # Ticker completo no Bloomberg
    'name': 'Nome Legivel',            # Nome para logs
    'lookback_days': 365,              # Periodo inicial de coleta (dias)
    'description': 'Descricao',        # O que o ticker representa
}
```

**Descobrindo tickers Bloomberg:**
- Use o Bloomberg Terminal (comando: DES <ticker>)
- Documentacao Bloomberg API
- Lista de tickers: https://www.bloomberg.com/markets

---

## Requisitos e Instalacao

### Requisitos

1. **Bloomberg Terminal ativo** (licenca necessaria)
2. **xbbg** instalado

### Instalacao

```bash
pip install xbbg
```

**Nota:** O Bloomberg Terminal precisa estar aberto e conectado para que a coleta funcione.

---

## Notas Importantes

1. **Licenca Bloomberg**: Requer assinatura paga do Bloomberg Terminal
2. **Terminal ativo**: O Terminal precisa estar aberto durante a coleta
3. **Lookback configuravel**: Cada ticker pode ter periodo inicial diferente
4. **Atualizacao incremental**: Coleta apenas dados novos apos primeira execucao
5. **Timezone**: Dados sao convertidos para timezone local sem offset

---

## Exemplo Completo

```python
from src.bloomberg import BloombergCollector
from core.indicators import list_indicators, BLOOMBERG_CONFIG

# Listar tickers disponiveis
tickers = list_indicators(BLOOMBERG_CONFIG)
print(f"Tickers disponiveis: {tickers}")

# Inicializar collector
collector = BloombergCollector('data/')

# Coletar todos os tickers
results = collector.collect()
print(f"Coletados: {list(results.keys())}")

# Consolidar dados
df_consolidated = collector.consolidate()
print(df_consolidated.head())

# Ver status dos arquivos
status = collector.get_status()
print(status)
```
