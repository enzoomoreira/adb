# Estendendo o Projeto

Guia para adicionar novos indicadores e criar novos providers.

---

## 1. Adicionar Indicadores a um Provider Existente

A forma mais simples de estender o projeto. Basta editar o `indicators.py` do provider.

### Localizacao

- SGS: `src/adb/providers/bacen/sgs/indicators.py`
- Expectations: `src/adb/providers/bacen/expectations/indicators.py`
- SIDRA: `src/adb/providers/ibge/sidra/indicators.py`
- IPEA: `src/adb/providers/ipea/indicators.py`
- Bloomberg: `src/adb/providers/bloomberg/indicators.py`

### Exemplo: Adicionar indicador SGS

```python
# src/adb/providers/bacen/sgs/indicators.py

SGS_CONFIG = {
    # Indicadores existentes...

    # NOVO INDICADOR
    "ipca_mensal": {
        "code": 433,                      # Codigo SGS do BCB
        "name": "IPCA Mensal",            # Nome para display
        "frequency": "monthly",           # daily | monthly | quarterly
        "description": "Variacao mensal do IPCA",
    },
}
```

### Campos Obrigatorios por Provider

| Provider | Campos Obrigatorios |
|----------|---------------------|
| SGS | `code` (int), `name` (str), `frequency` (str) |
| Expectations | `endpoint` (str), `indicator` (str), `name` (str), `frequency` (str) |
| SIDRA | `name` (str), `frequency` (str), `parameters` (dict) |
| IPEA | `code` (str), `name` (str), `frequency` (str) |
| Bloomberg | `ticker` (str), `fields` (list), `name` (str), `frequency` (str) |

### Testar

```python
import adb

print(adb.sgs.available())       # Deve incluir 'ipca_mensal'
print(adb.sgs.info('ipca_mensal'))

df = adb.sgs.fetch('ipca_mensal', start='2024')  # Stateless
adb.sgs.collect('ipca_mensal')                     # Persistir
df = adb.sgs.read('ipca_mensal')                   # Ler do cache
```

---

## 2. Criar um Novo Provider

Um provider precisa de 3 arquivos (sem collector -- o BaseCollector e generico):

```
src/adb/providers/nova_fonte/
    __init__.py        # Vazio (package marker)
    indicators.py      # Catalogo de indicadores
    client.py          # Comunicacao com API
    explorer.py        # Interface publica (~15 linhas)
```

### Passo 1: indicators.py

```python
# src/adb/providers/nova_fonte/indicators.py

NOVA_FONTE_CONFIG = {
    "indicador_1": {
        "code": "CODIGO_API",
        "name": "Nome do Indicador",
        "frequency": "daily",
        "description": "Descricao do indicador",
    },
    "indicador_2": {
        "code": "OUTRO_CODIGO",
        "name": "Outro Indicador",
        "frequency": "monthly",
    },
}
```

### Passo 2: client.py

O client deve implementar `get_data(config, start_date, end_date) -> DataFrame`.
Recebe o dict de config completo e extrai os campos que precisa internamente.

```python
# src/adb/providers/nova_fonte/client.py

import httpx
import pandas as pd

from adb.infra.log import get_logger
from adb.infra.resilience import retry


class NovaFonteClient:
    """Cliente para a API da Nova Fonte."""

    BASE_URL = "https://api.novafonte.com/v1"

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @retry(max_attempts=3, delay=1.0)
    def get_data(
        self,
        config: dict,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """Busca dados de um indicador.

        Args:
            config: Dict do indicador com code, name, frequency.
            start_date: Data inicial 'YYYY-MM-DD'.
            end_date: Data final 'YYYY-MM-DD'.

        Returns:
            DataFrame com DatetimeIndex + coluna 'value'.
        """
        code = config["code"]

        params = {"codigo": code}
        if start_date:
            params["inicio"] = start_date
        if end_date:
            params["fim"] = end_date

        response = httpx.get(f"{self.BASE_URL}/series", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["data"])
        df["value"] = pd.to_numeric(df["valor"])
        df = df.set_index("date")[["value"]].sort_index()

        return df
```

### Passo 3: explorer.py

O explorer e minimo -- declara 4 atributos e nada mais.

```python
# src/adb/providers/nova_fonte/explorer.py

from adb.explorer import BaseExplorer
from .indicators import NOVA_FONTE_CONFIG


class NovaFonteExplorer(BaseExplorer):
    """Explorer para dados da Nova Fonte."""

    _CONFIG = NOVA_FONTE_CONFIG
    _SUBDIR_TEMPLATE = "nova_fonte/{frequency}"
    _TITLE = "Nova Fonte - Dados"

    @property
    def _CLIENT_CLASS(self):
        from .client import NovaFonteClient
        return NovaFonteClient
```

O BaseExplorer herda tudo: `read()`, `fetch()`, `collect()`, `available()`, `info()`, `status()`.
O BaseCollector e criado automaticamente pelo `collect()` usando os atributos do explorer.

---

## 3. Registrar o Novo Provider

Adicionar uma entrada no registry em `src/adb/__init__.py`:

```python
_EXPLORER_REGISTRY: dict[str, tuple[str, str]] = {
    "sgs": ("adb.providers.bacen.sgs.explorer", "SGSExplorer"),
    # ... providers existentes ...

    # NOVO PROVIDER
    "nova_fonte": ("adb.providers.nova_fonte.explorer", "NovaFonteExplorer"),
}
```

Pronto. `adb.nova_fonte.read()`, `adb.nova_fonte.fetch()`, `adb.nova_fonte.collect()` funcionam automaticamente.

---

## Checklist

- [ ] Criar `indicators.py` com `_CONFIG` dict
- [ ] Criar `client.py` com `get_data(config, start_date, end_date) -> DataFrame`
- [ ] Criar `explorer.py` herdando BaseExplorer (4 atributos: `_CONFIG`, `_SUBDIR_TEMPLATE`, `_TITLE`, `_CLIENT_CLASS`)
- [ ] Adicionar entrada no `_EXPLORER_REGISTRY` em `__init__.py`
- [ ] Testar: `available()`, `fetch()`, `collect()`, `read()`, `status()`
