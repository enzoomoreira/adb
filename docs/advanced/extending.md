# Estendendo o Projeto

Guia para desenvolvedores sobre como adicionar novos indicadores e criar novos providers.

## Arquitetura do Projeto

O projeto segue Clean Architecture com separacao clara de responsabilidades:

```
src/adb/
├── domain/           # Regras de negocio (BaseExplorer, Exceptions)
├── infra/            # Infraestrutura (Config, Log, Persistence)
├── services/         # Logica de aplicacao (BaseCollector, Registry)
├── providers/        # Implementacoes por fonte de dados
│   ├── bacen/
│   │   ├── sgs/
│   │   └── expectations/
│   ├── ibge/sidra/
│   ├── ipea/
│   └── bloomberg/
├── shared/           # Utilitarios compartilhados
└── ui/               # Interface visual (Rich)
```

---

## 1. Adicionar Indicadores a um Provider Existente

A forma mais simples de estender o projeto e adicionar novos indicadores a providers ja existentes.

### Passo 1: Editar o arquivo indicators.py

Cada provider tem um arquivo `indicators.py` com a configuracao dos indicadores.

**Localizacao:**
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
    "selic": {
        "code": 432,
        "name": "Meta Selic",
        "frequency": "daily",
        "description": "Taxa basica de juros da economia brasileira",
    },

    # NOVO INDICADOR
    "ipca_mensal": {
        "code": 433,                      # Codigo SGS do BCB
        "name": "IPCA Mensal",            # Nome para display
        "frequency": "monthly",           # daily | monthly | quarterly
        "description": "Variacao mensal do IPCA",  # Descricao (opcional)
    },
}
```

### Campos Obrigatorios por Provider

| Provider | Campos Obrigatorios |
|----------|---------------------|
| SGS | `code` (int), `name` (str), `frequency` (str) |
| Expectations | `indicador` (str), `name` (str) |
| SIDRA | `code` (int), `name` (str), `frequency` (str), `parameters` (dict) |
| IPEA | `code` (str), `name` (str), `frequency` (str) |
| Bloomberg | `ticker` (str), `name` (str), `frequency` (str) |

### Passo 2: Testar

```python
import adb

# Verificar se o indicador aparece
print(adb.sgs.available())  # Deve incluir 'ipca_mensal'

# Ver info
print(adb.sgs.info('ipca_mensal'))

# Coletar
adb.sgs.collect('ipca_mensal')

# Ler
df = adb.sgs.read('ipca_mensal')
```

---

## 2. Criar um Novo Provider

Para adicionar uma nova fonte de dados, voce precisa criar 4 arquivos:

1. `client.py` - Comunicacao com a API externa
2. `collector.py` - Orquestracao da coleta
3. `explorer.py` - Interface de leitura
4. `indicators.py` - Configuracao dos indicadores

### Estrutura do Provider

```
src/adb/providers/
└── nova_fonte/
    ├── __init__.py
    ├── client.py
    ├── collector.py
    ├── explorer.py
    └── indicators.py
```

### Passo 1: Criar indicators.py

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

### Passo 2: Criar client.py

O client encapsula a comunicacao com a API externa.

```python
# src/adb/providers/nova_fonte/client.py

import httpx
import pandas as pd

from adb.infra.log import get_logger
from adb.infra.resilience import retry


class NovaFonteClient:
    """
    Cliente para a API da Nova Fonte.

    Responsabilidades:
    - Comunicacao HTTP com a API
    - Parsing de respostas
    - Retry automatico em erros transientes
    """

    BASE_URL = "https://api.novafonte.com/v1"

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    @retry(max_attempts=3, delay=1.0)
    def get_data(
        self,
        code: str,
        name: str,
        frequency: str,
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        Busca dados de um indicador.

        Args:
            code: Codigo do indicador na API
            name: Nome para a coluna (usado internamente)
            frequency: 'daily' ou 'monthly'
            start_date: Data inicial 'YYYY-MM-DD' (opcional)

        Returns:
            DataFrame com colunas ['date', 'value'] (convencao interna de storage;
            o explorer renomeia 'value' para o nome do indicador no read())
        """
        params = {"codigo": code}
        if start_date:
            params["inicio"] = start_date

        try:
            response = httpx.get(
                f"{self.BASE_URL}/series",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # Converter para DataFrame padrao
            df = pd.DataFrame(data)
            df = df.rename(columns={"data": "date", "valor": "value"})
            df["date"] = pd.to_datetime(df["date"])

            return df

        except httpx.HTTPError as e:
            self.logger.error(f"Erro ao buscar {name}: {e}")
            raise  # Re-raise para retry funcionar
```

### Passo 3: Criar collector.py

O collector usa o padrao **Template Method**: herda `collect()` do `BaseCollector` e implementa apenas `_collect_one()` para a logica especifica de cada indicador.

```python
# src/adb/providers/nova_fonte/collector.py

from pathlib import Path
import pandas as pd

from adb.services.collectors import BaseCollector
from .client import NovaFonteClient
from .indicators import NOVA_FONTE_CONFIG


class NovaFonteCollector(BaseCollector):
    """
    Coletor de dados da Nova Fonte.

    Usa template method do BaseCollector:
    - collect() e herdado (normalize -> start -> loop _collect_one -> end)
    - status() auto-deriva subdirs do _CONFIG via _subdir_for()
    """

    _CONFIG = NOVA_FONTE_CONFIG
    _TITLE = "Nova Fonte - Coleta de Dados"
    default_subdir = 'nova_fonte/daily'

    def __init__(self, data_path: Path | None = None):
        super().__init__(data_path)
        self.client = NovaFonteClient()

    def _collect_one(self, key: str, config: dict, start: str | None, end: str | None, save: bool, verbose: bool) -> None:
        """Coleta um indicador individual."""
        frequency = config.get('frequency', 'daily')
        subdir = self._subdir_for(key)

        self._persist(
            fetch_fn=lambda start_date, end_date: self.client.get_data(
                code=config['code'],
                name=config['name'],
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
            ),
            filename=key,
            name=config['name'],
            subdir=subdir,
            frequency=frequency,
            start=start,
            end=end,
            save=save,
            verbose=verbose,
        )

    def _subdir_for(self, key: str) -> str:
        """Subdir dinamico baseado na frequencia do indicador."""
        freq = self._CONFIG[key].get('frequency', 'daily')
        return f"nova_fonte/{freq}"

    def _get_frequency_for_file(self, filename: str) -> str | None:
        """Retorna frequencia de um indicador (usado pelo DataValidator)."""
        config = NOVA_FONTE_CONFIG.get(filename, {})
        return config.get('frequency', 'daily')
```

> **Nota:** `collect()` e `status()` sao herdados do `BaseCollector`. O `status()` auto-deriva subdirs unicos chamando `_subdir_for()` para cada indicador do `_CONFIG`, sem necessidade de hardcodar listas de subdirs.

### Passo 4: Criar explorer.py

O explorer fornece a interface de leitura.

```python
# src/adb/providers/nova_fonte/explorer.py

from adb.domain.explorers import BaseExplorer
from .indicators import NOVA_FONTE_CONFIG


class NovaFonteExplorer(BaseExplorer):
    """
    Explorer para dados da Nova Fonte.

    Fornece interface pythonica:
        adb.nova_fonte.read('indicador_1')
        adb.nova_fonte.available()
        adb.nova_fonte.collect()
    """

    _CONFIG = NOVA_FONTE_CONFIG
    _SUBDIR = "nova_fonte/daily"  # Subdir padrao

    @property
    def _COLLECTOR_CLASS(self):
        """Retorna classe do collector (lazy import)."""
        from .collector import NovaFonteCollector
        return NovaFonteCollector

    def _subdir(self, indicator: str) -> str:
        """Subdir dinamico baseado em frequency."""
        freq = self._CONFIG[indicator].get('frequency', 'daily')
        return f"nova_fonte/{freq}"
```

### Passo 5: Criar __init__.py

```python
# src/adb/providers/nova_fonte/__init__.py

from .explorer import NovaFonteExplorer
from .collector import NovaFonteCollector
from .client import NovaFonteClient
from .indicators import NOVA_FONTE_CONFIG

__all__ = [
    'NovaFonteExplorer',
    'NovaFonteCollector',
    'NovaFonteClient',
    'NOVA_FONTE_CONFIG',
]
```

---

## 3. Registrar o Novo Provider

### Passo 1: Registrar no Registry

Adicione o collector ao registro em `src/adb/services/collectors/registry.py`:

```python
# src/adb/services/collectors/registry.py

_COLLECTOR_MAP = {
    'sgs': ('bacen.sgs.collector', 'SGSCollector'),
    'expectations': ('bacen.expectations.collector', 'ExpectationsCollector'),
    'ipea': ('ipea.collector', 'IPEACollector'),
    'bloomberg': ('bloomberg.collector', 'BloombergCollector'),
    'sidra': ('ibge.sidra.collector', 'SidraCollector'),

    # NOVO PROVIDER
    'nova_fonte': ('nova_fonte.collector', 'NovaFonteCollector'),
}
```

### Passo 2: Exportar no __init__.py principal

Adicione o explorer em `src/adb/__init__.py`:

```python
# src/adb/__init__.py

# ... imports existentes ...

# Adicionar variavel global
_nova_fonte = None

def __getattr__(name):
    global _sgs, _expectations, _ipea, _bloomberg, _sidra, _nova_fonte

    # ... cases existentes ...

    # NOVO PROVIDER
    if name == 'nova_fonte':
        if _nova_fonte is None:
            from adb.providers.nova_fonte.explorer import NovaFonteExplorer
            _nova_fonte = NovaFonteExplorer()
        return _nova_fonte

    raise AttributeError(f"module 'adb' has no attribute '{name}'")


def available_sources() -> list[str]:
    """Lista todas as fontes de dados disponiveis."""
    return ['sgs', 'expectations', 'ipea', 'bloomberg', 'sidra', 'nova_fonte']


__all__ = [
    # ... exports existentes ...
    'nova_fonte',
]
```

---

## 4. Testes

### Estrutura de Testes

```
tests/
└── providers/
    └── nova_fonte/
        ├── test_client.py
        ├── test_collector.py
        └── test_explorer.py
```

### Exemplo de Teste

```python
# tests/providers/nova_fonte/test_explorer.py

import pytest
from adb.providers.nova_fonte.explorer import NovaFonteExplorer
from adb.providers.nova_fonte.indicators import NOVA_FONTE_CONFIG


class TestNovaFonteExplorer:
    def test_available_returns_all_indicators(self):
        explorer = NovaFonteExplorer()
        available = explorer.available()

        assert len(available) == len(NOVA_FONTE_CONFIG)
        assert 'indicador_1' in available

    def test_info_returns_config(self):
        explorer = NovaFonteExplorer()
        info = explorer.info('indicador_1')

        assert info['code'] == NOVA_FONTE_CONFIG['indicador_1']['code']
        assert 'frequency' in info
```

---

## Checklist de Implementacao

- [ ] Criar `indicators.py` com configuracao
- [ ] Criar `client.py` com comunicacao API
- [ ] Criar `collector.py` herdando de BaseCollector (definir `_CONFIG`, `_TITLE`, `_collect_one()`)
- [ ] Criar `explorer.py` herdando de BaseExplorer
- [ ] Criar `__init__.py` com exports
- [ ] Registrar em `services/collectors/registry.py`
- [ ] Exportar em `src/adb/__init__.py`
- [ ] (Opcional) Escrever testes

---

## Proximos Passos

- [Queries Avancadas](querying.md) - Como usar o QueryEngine diretamente
- Consulte os providers existentes como referencia de implementacao
