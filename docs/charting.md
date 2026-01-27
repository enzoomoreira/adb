# Modulo Charting (Visualizacao)

Documentacao do modulo de visualizacao do Agora-Database.

## Visao Geral

O modulo `src/adb/core/charting/` fornece uma interface fluida para geracao de graficos padronizados, seguindo a identidade visual da Agora Investimentos.

Ele opera atraves do padrao **Pandas Accessor**, permitindo chamar funcoes de plotagem diretamente em DataFrames.

---

## Uso Basico

```python
import adb.core.charting  # Necessario para registrar o acessor .agora

# 1. Leitura de dados
df = adb.sgs.read('selic')

# 2. Plotagem automatica
df.agora.plot(title="Taxa Selic Meta")

# 3. Salvar grafico
df.agora.save("output/charts/selic.png")
```

---

## Interface (Accessor)

O acessor `.agora.plot()` aceita os seguintes argumentos:

```python
df.agora.plot(
    x: str = None,              # Coluna para eixo X (padrao: usa o index)
    y: str | list[str] = None,  # Coluna(s) para eixo Y (padrao: todas numericas)
    kind: str = 'line',         # Tipo de grafico: 'line' ou 'bar'
    title: str = None,          # Titulo do grafico
    units: str = None,          # Formatacao do eixo Y: 'BRL', 'USD', '%', 'points', 'human'
    source: str = None,         # Fonte dos dados para rodape (ex: 'BCB', 'IBGE')
    highlight_last: bool = False,  # Destaca ultimo valor com ponto e label (apenas line)
    y_origin: str = 'zero',     # Origem do eixo Y para barras: 'zero' ou 'auto'
    save_path: str = None,      # Caminho para salvar a imagem (opcional)
    **kwargs                    # Argumentos extras repassados para matplotlib
)
```

**Retorno:** Objeto `matplotlib.axes.Axes`

### Exemplos

#### Grafico de Linhas (Padrao)

```python
df = adb.sgs.read('selic', 'cdi')
df.agora.plot(
    title="Juros: Selic vs CDI",
    units='%',
    source='BCB'
)
```

#### Grafico com Destaque no Ultimo Valor

```python
df.agora.plot(
    title="IPCA Acumulado 12m",
    units='%',
    highlight_last=True,
    source='IBGE'
)
```

#### Grafico de Barras

```python
df_saldo.agora.plot(
    kind='bar',
    title="Saldo do CAGED",
    units='human',
    y_origin='auto',
    source='MTE'
)
```

#### Salvando a Imagem

```python
# Opcao 1: via parametro
df.agora.plot(
    title="Exportacao Automatica",
    save_path="output/charts/meu_grafico.png"
)

# Opcao 2: via metodo save()
df.agora.plot(title="Meu Grafico")
df.agora.save("output/charts/meu_grafico.png")
```

---

## Transformacoes de Series Temporais

O modulo exporta funcoes utilitarias para transformacao de dados antes da plotagem:

```python
from adb.core.charting import yoy, mom, accum_12m, diff, normalize
```

| Funcao | Descricao | Exemplo |
|--------|-----------|---------|
| `yoy(df, periods=12)` | Variacao percentual ano contra ano | `yoy(df).agora.plot()` |
| `mom(df, periods=1)` | Variacao percentual mes contra mes | `mom(df).agora.plot()` |
| `accum_12m(df)` | Variacao acumulada em 12 meses | `accum_12m(df).agora.plot()` |
| `diff(df, periods=1)` | Diferenca absoluta entre periodos | `diff(df).agora.plot()` |
| `normalize(df, base=100, base_date=None)` | Normaliza para valor base em data especifica | `normalize(df, base_date='2020-01-01').agora.plot()` |

---

## Formatadores do Eixo Y

O parametro `units` controla a formatacao dos valores no eixo Y:

| Valor | Formato | Exemplo |
|-------|---------|---------|
| `'BRL'` | Real brasileiro | R$ 1.234,56 |
| `'USD'` | Dolar americano | $ 1,234.56 |
| `'%'` | Percentual | 10,5% |
| `'points'` | Pontos base | 10.5 p.p. |
| `'human'` | Notacao abreviada | 1.2M, 500k |

---

## Tema e Estilizacao

O modulo aplica automaticamente o tema institucional da Agora Investimentos (`src/adb/core/charting/styling/`).

### Paleta de Cores

```python
ColorPalette:
  primary:     "#00464D"   # Verde escuro institucional
  secondary:   "#006B6B"   # Verde medio
  tertiary:    "#008B8B"   # Teal
  quaternary:  "#20B2AA"   # Light sea green
  quinary:     "#5F9EA0"   # Cadet blue
  senary:      "#2E8B57"   # Sea green

  # Cores semanticas
  text:        "#00464D"   # Texto (igual primary)
  grid:        "lightgray" # Linhas de grade
  background:  "white"     # Fundo
  positive:    "#00464D"   # Valores positivos
  negative:    "#8B0000"   # Valores negativos (vermelho discreto)
```

### Configuracoes do Tema

- **Fonte**: BradescoSans-Light (carregada de `assets/fonts/`) ou fallback para sans-serif
- **Tamanho de fonte**: 11pt (geral), 18pt (titulos)
- **Estilo base**: seaborn-v0_8-white
- **Layout**: Minimalista (bordas superior/direita desabilitadas, fundo branco)
- **Tamanho padrao**: 10x6 polegadas

---

## Componentes

### Rodape (Footer)

Quando o parametro `source` e fornecido, um rodape e adicionado automaticamente:

```
Fonte: BCB, Agora Investimentos
```

Sem source, exibe apenas:
```
Agora Investimentos
```

### Marcadores (Markers)

Com `highlight_last=True`, o ultimo ponto de dados e destacado com:
- Ponto circular (scatter)
- Label com valor formatado (usando o formatador do eixo Y)

---

## Arquitetura

```
src/adb/core/charting/
├── __init__.py           # Exports do modulo
├── accessor.py           # Registra a extensao df.agora no Pandas
├── engine.py             # AgoraPlotter - logica principal de plotagem
├── config.py             # Configuracao (CHARTS_PATH)
├── transforms.py         # Transformacoes de series temporais
├── assets/
│   └── fonts/
│       └── BradescoSans-Light.ttf
├── components/
│   ├── footer.py         # Componente de rodape
│   └── markers.py        # Destaque de pontos
├── plots/
│   ├── line.py           # Implementacao de grafico de linhas
│   └── bar.py            # Implementacao de grafico de barras
└── styling/
    ├── theme.py          # Paleta de cores e tema
    ├── fonts.py          # Carregamento de fontes
    └── formatters.py     # Formatadores de eixo Y
```

### Principais Classes

| Classe | Arquivo | Responsabilidade |
|--------|---------|------------------|
| `AgoraAccessor` | accessor.py | Registra `df.agora` e delega para o plotter |
| `AgoraPlotter` | engine.py | Orquestra a construcao dos graficos |
| `ColorPalette` | styling/theme.py | Define a paleta de cores institucional |
| `AgoraTheme` | styling/theme.py | Aplica o tema no matplotlib |

---

## Exports do Modulo

```python
from adb.core.charting import (
    AgoraAccessor,    # Classe do accessor
    AgoraPlotter,     # Engine (uso avancado)
    theme,            # Instancia global do tema
    CHARTS_PATH,      # Diretorio de saida
    # Transformacoes
    yoy,
    mom,
    accum_12m,
    diff,
    normalize,
)
```
