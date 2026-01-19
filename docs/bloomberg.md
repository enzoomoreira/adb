# Modulo Bloomberg Terminal

Documentacao do coletor de dados do Bloomberg Terminal.

## Visao Geral

O modulo `src/bloomberg/` coleta dados de mercado financeiro via Bloomberg Terminal.

| Caracteristica | Valor |
|----------------|-------|
| Fonte | Bloomberg Terminal (xbbg) |
| Formato | Series temporais |
| Foco | Dados de mercado financeiro (equities, commodities) |
| Requisito | Bloomberg Terminal ativo |

---

## Arquitetura de Uso

### Para Coleta de Dados

```python
from core.collectors import collect

collect('bloomberg')                              # Todos indicadores
collect('bloomberg', indicators='brent')          # Um indicador
collect('bloomberg', indicators=['brent', 'gold'])  # Lista
```

### Para Leitura/Queries (Explorer)

```python
from core.data import bloomberg

df = bloomberg.read('brent')                    # Leitura simples
df = bloomberg.read('brent', start='2024')      # Com filtro de data
df = bloomberg.read('brent', 'gold')            # Multiplos indicadores
print(bloomberg.available())                    # Lista indicadores
print(bloomberg.available(category='commodities'))  # Por categoria
print(bloomberg.info('brent'))                  # Info do indicador
```

---

## BLOOMBERG_CONFIG

Indicadores disponiveis em `src/bloomberg/indicators.py`:

### Global Equities

| Chave | Ticker | Nome | Campo |
|-------|--------|------|-------|
| msci_acwi_mktcap | MXWD Index | MSCI ACWI - Market Cap | CUR_MKT_CAP |
| msci_acwi_pe | MXWD Index | MSCI ACWI - P/E Ratio | BEST_PE_RATIO |
| msci_acwi_dividend | MXWD Index | MSCI ACWI - Dividend Yield | EQY_DVD_YLD_12M |

### Brasil Equities

| Chave | Ticker | Nome | Campo |
|-------|--------|------|-------|
| ibov_points | IBOV Index | Ibovespa - Pontos | PX_LAST |
| ibov_usd | USIBOV Index | Ibovespa - USD | PX_LAST |
| ifix | IFIX Index | IFIX | PX_LAST |

### Commodities

| Chave | Ticker | Nome | Campo |
|-------|--------|------|-------|
| brent | CO1 Comdty | Brent Crude | PX_LAST |
| iron_ore | SCOA Comdty | Iron Ore | PX_LAST |
| gold | XAU Curncy | Gold Spot | PX_LAST |

### Funcoes Auxiliares

```python
from src.bloomberg import BLOOMBERG_CONFIG
from core import list_indicators, get_indicator_config, filter_by_field

list_indicators(BLOOMBERG_CONFIG)                         # Lista chaves
get_indicator_config(BLOOMBERG_CONFIG, 'brent')           # Config completa
filter_by_field(BLOOMBERG_CONFIG, 'category', 'commodities')  # Por categoria
```

---

## Uso Avancado (Acesso Direto)

Para casos especiais:

```python
# Collector (import direto - uso interno)
from bloomberg.collector import BloombergCollector

collector = BloombergCollector(data_path='data/')
results = collector.collect('brent')
collector.get_status()

# Client (baixo nivel)
from bloomberg.client import BloombergClient

client = BloombergClient()
df = client.get_data(
    ticker='CO1 Comdty',
    field='PX_LAST',
    name='Brent',
    start_date='2024-01-01',
)
```

### BloombergCollector.collect()

```python
def collect(
    indicators: list[str] | str = 'all',
    save: bool = True,
    verbose: bool = True,
) -> dict[str, pd.DataFrame]
```

### BloombergClient.get_data()

```python
def get_data(
    ticker: str,
    field: str,
    name: str = None,
    start_date: str = None,
    end_date: str = None,
    verbose: bool = False,
) -> pd.DataFrame
```

---

## Exports Publicos

```python
# Config (exportado)
from src.bloomberg import BLOOMBERG_CONFIG

# Funcoes auxiliares (centralizadas em core)
from core import list_indicators, get_indicator_config, filter_by_field

# Interface centralizada (recomendado)
from core.collectors import collect
from core.data import bloomberg
```

---

## Arquivos Gerados

```
data/
└── raw/
    └── bloomberg/
        └── daily/
            ├── msci_acwi_mktcap.parquet
            ├── msci_acwi_pe.parquet
            ├── msci_acwi_dividend.parquet
            ├── ibov_points.parquet
            ├── ibov_usd.parquet
            ├── ifix.parquet
            ├── brent.parquet
            ├── iron_ore.parquet
            └── gold.parquet
```

---

## Extensibilidade

Para adicionar novos tickers Bloomberg:

```python
# Em src/bloomberg/indicators.py
BLOOMBERG_CONFIG['novo_ticker'] = {
    'ticker': 'TICKER Index',       # Ticker Bloomberg
    'fields': ['PX_LAST'],          # Campos a coletar
    'name': 'Nome Legivel',
    'frequency': 'daily',
    'description': 'Descricao',
    'category': 'categoria',        # global_equities, brazil_equities, commodities
}
```

---

## Requisitos

1. **Bloomberg Terminal ativo** (licenca necessaria)
2. **xbbg** instalado: `pip install xbbg`

**Nota:** O Bloomberg Terminal precisa estar aberto e conectado para que a coleta funcione.
