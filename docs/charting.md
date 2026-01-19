# Modulo Charting (Visualizacao)

Documentacao do modulo de visualizacao do Agora-Database.

## Visao Geral

O modulo `src/core/charting/` fornece uma interface fluida para geracao de graficos padronizados, seguindo a identidade visual do projeto.

Ele opera atraves do padrão **Pandas Accessor**, permitindo chamar funcões de plotagem diretamente em DataFrames retornados pelos explorers.

---

## Uso Basico

```python
import core.charting # Necessario para registrar o acessor .agora
from core.data import sgs

# 1. Leitura de dados
df = sgs.read('selic')

# 2. Plotagem automatica
df.agora.plot(title="Taxa Selic Meta")
```

---

## Interface (Accessor)

O acessor `.agora.plot()` aceita os seguintes argumentos:

```python
df.agora.plot(
    kind: str = 'line',        # Tipo de grafico: 'line' ou 'bar'
    title: str = None,         # Titulo do grafico
    save_path: str = None,     # Caminho para salvar a imagem (opcional)
    **kwargs                   # Argumentos extras repassados para matplotlib
)
```

### Exemplos

#### Grafico de Linhas (Padrao)

```python
df = sgs.read('selic', 'cdi')
df.agora.plot(
    title="Juros: Selic vs CDI",
    ylabel="Taxa (% a.a.)"
)
```

#### Grafico de Barras

```python
# Supondo um dataframe de saldo mensal
df_saldo.agora.plot(
    kind='bar',
    title="Saldo do CAGED",
    color='steelblue'
)
```

#### Salvando a Imagem

```python
df.agora.plot(
    title="Exportacao Automatica",
    save_path="output/imgs/meu_grafico.png"
)
```

---

## Tema e Estilização

O modulo aplica automaticamente um tema padronizado (`src/core/charting/theme.py`) que define:

- **Fonte**: BradescoSans-Light (se disponivel na pasta assets)
- **Cores**: 
    - Primaria: `#00464D` (Verde escuro institucional)
    - Texto/Eixos: `#00464D`
    - Grid: `lightgray`
- **Layout**: Minimalista (sem bordas superior/direita, fundo branco).

---

## Arquitetura

O modulo e composto por:

1.  **Accessor (`accessor.py`)**: Registra a extensao `df.agora` no Pandas.
2.  **Plotter (`plotter.py`)**: Implementa a logica de construcao dos graficos usando Matplotlib.
3.  **Theme (`theme.py`)**: Centraliza as definicoes de estilo e carregamento de fontes.

Esta separacao garante que o codigo de visualizacao fique desacoplado da logica de recuperacao de dados.
