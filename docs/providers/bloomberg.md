# Bloomberg Terminal

Dados de mercado financeiro via Bloomberg Terminal.

## Visao Geral

| Caracteristica | Valor |
|----------------|-------|
| Fonte | Bloomberg Terminal (via xbbg) |
| Dados | Series temporais de mercado financeiro |
| Categorias | Equities globais, equities Brasil, commodities |
| Requisito | Bloomberg Terminal ativo para coleta |

**Importante:** A coleta requer o Bloomberg Terminal aberto e conectado. A leitura de dados ja salvos funciona offline.

---

## Indicadores Disponiveis

### Global Equities

| Indicador | Nome | Descricao |
|-----------|------|-----------|
| `msci_acwi_mktcap` | MSCI ACWI - Market Cap | Capitalizacao de mercado global |
| `msci_acwi_pe` | MSCI ACWI - P/E Ratio | Multiplo preco/lucro global |
| `msci_acwi_dividend` | MSCI ACWI - Dividend Yield | Rendimento de dividendos global |

### Brasil Equities

| Indicador | Nome | Descricao |
|-----------|------|-----------|
| `ibov_points` | Ibovespa - Pontos | Indice Bovespa em pontos |
| `ibov_usd` | Ibovespa - USD | Indice Bovespa em dolares |
| `ifix` | IFIX | Indice de fundos imobiliarios |

### Commodities

| Indicador | Nome | Descricao |
|-----------|------|-----------|
| `brent` | Brent Crude | Petroleo Brent |
| `iron_ore` | Iron Ore | Minerio de ferro |
| `gold` | Gold Spot | Ouro spot |

---

## Exemplos de Uso

### Coletar Dados

```python
import adb

# Coleta todos os indicadores configurados
adb.bloomberg.collect()

# Coleta um indicador especifico
adb.bloomberg.collect(indicators='brent')

# Coleta multiplos indicadores
adb.bloomberg.collect(indicators=['brent', 'gold', 'ibov_points'])
```

A coleta e incremental: se ja existem dados salvos, apenas registros novos sao baixados.

### Leitura de Dados

```python
import adb

# Leitura simples
df = adb.bloomberg.read('brent')

# Leitura com filtro de data
df = adb.bloomberg.read('brent', start='2024-01-01')
df = adb.bloomberg.read('brent', start='2024', end='2024-06-30')

# Multiplos indicadores
df = adb.bloomberg.read('brent', 'gold')
df = adb.bloomberg.read('brent', 'gold', 'ibov_points', start='2024')
```

### Consultas e Status

```python
import adb

# Listar indicadores disponiveis
adb.bloomberg.available()
# ['brent', 'gold', 'ibov_points', ...]

# Filtrar por categoria
adb.bloomberg.available(category='commodities')
# ['brent', 'iron_ore', 'gold']

adb.bloomberg.available(category='brazil_equities')
# ['ibov_points', 'ibov_usd', 'ifix']

# Informacoes de um indicador
adb.bloomberg.info('brent')
# {
#     'ticker': 'CO1 Comdty',
#     'fields': ['PX_LAST'],
#     'name': 'Brent Crude',
#     'frequency': 'daily',
#     'category': 'commodities'
# }

# Status dos arquivos salvos
adb.bloomberg.get_status()
```

---

## Arquivos Gerados

Apos a coleta, os dados sao salvos em:

```
data/raw/bloomberg/daily/
    msci_acwi_mktcap.parquet
    msci_acwi_pe.parquet
    msci_acwi_dividend.parquet
    ibov_points.parquet
    ibov_usd.parquet
    ifix.parquet
    brent.parquet
    iron_ore.parquet
    gold.parquet
```

Cada arquivo contem a serie temporal completa do indicador.

---

## Notas Importantes

### Requisitos para Coleta

1. **Bloomberg Terminal** instalado e ativo (licenca necessaria)
2. Terminal **aberto e conectado** durante a coleta
3. Pacote `xbbg` instalado

Se voce nao tem acesso ao Bloomberg Terminal, pode usar os dados ja coletados (leitura funciona offline).

### Lookback Padrao

Por padrao, a coleta busca 2 anos de historico (730 dias) para novos indicadores. Atualizacoes posteriores buscam apenas dados novos desde a ultima coleta.

### Funcionamento Offline

A **leitura** de dados ja salvos funciona sem conexao com o Bloomberg:

```python
import adb

# Funciona offline se os dados ja foram coletados
df = adb.bloomberg.read('brent')
```

Apenas a **coleta** requer o Terminal ativo:

```python
import adb

# Requer Bloomberg Terminal ativo
adb.bloomberg.collect('brent')
```
