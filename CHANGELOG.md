# Changelog

## [2026-03-25 21:06]

Refatoracao inspirada no OpenBB Platform: padronizar interface de clients,
eliminar collectors concretos, e simplificar estrutura de pastas.

### Added

- **`Client.get_data(config, start, end)`**: interface padrao em todos os 5 clients.
  Cada client recebe o dict de config do indicador e extrai internamente o que precisa,
  eliminando a necessidade de cada collector saber quais campos extrair.
- **`ExpectationsClient.get_data()`**: novo metodo que wrappa `query()` para seguir
  a interface padrao dos demais clients.
- **`_SUBDIR_TEMPLATE`** no BaseExplorer: template string (ex: `"bacen/sgs/{frequency}"`)
  que resolve subdir automaticamente a partir do frequency do config.
- **`_CLIENT_CLASS`** e **`_TITLE`** como atributos do BaseExplorer: explorer declara
  qual client e titulo usar, BaseCollector e criado parametricamente.
- **Registry pattern no `__init__.py`**: dict + importlib substitui lazy loading manual
  com variaveis globais. Adicionar provider = adicionar entrada no dict.

### Removed

- **5 collectors concretos**: `SGSCollector`, `IPEACollector`, `SidraCollector`,
  `BloombergCollector`, `ExpectationsCollector`. BaseCollector agora e generico
  e recebe config/title/client_class/subdir_template no construtor.
- **`services/collectors/registry.py`**: dead code, nao era importado em nenhum lugar.
- **`shared/utils/indicators.py`** (`get_config()`): unico caller era o antigo BaseCollector.
- **`RateLimitError`** e **`ConnectionFailedError`**: definidas mas nunca usadas. O `@retry`
  absorve erros transientes sem precisar de excecoes especificas.
- **Camadas `domain/`, `services/`, `shared/`, `ui/`**: eliminadas por conter 1 arquivo cada.
  Arquivos promovidos ao nivel do pacote (`explorer.py`, `collector.py`, `utils.py`, `display.py`).
- **`infra/persistence/`**: flatten -- `query.py`, `storage.py`, `validation.py` sobem para `infra/`.
- **7 `__init__.py` intermediarios** e **7 diretorios vazios** removidos.

### Changed

- **BaseCollector**: de abstract class com `_collect_one()` para classe concreta parametrizada.
  O Explorer cria instancias passando config/title/client/subdir no construtor.
  `_collect_one()` agora e generico e chama `client.get_data(config, start, end)`.
- **BaseExplorer._fetch_one()**: implementacao generica na base class usando `_CLIENT_CLASS`.
  Apenas `ExpectationsExplorer` mantem override (read/join/fetch customizados).
- **5 clients refatorados**: assinatura mudou de parametros individuais
  (`code, name, frequency, start, end`) para `(config: dict, start, end)`.
- **SidraClient.get_data()**: agora recebe config completo e extrai `config["parameters"]`
  internamente (antes recebia o subdict `parameters` diretamente).
- **Explorers simplificados**: 4 explorers (SGS, IPEA, Sidra, Bloomberg) reduzidos a
  ~15 linhas cada -- declaram `_CONFIG`, `_SUBDIR_TEMPLATE`, `_TITLE`, `_CLIENT_CLASS`.
- **Imports atualizados**: todos os 18 imports internos atualizados para refletir nova
  estrutura (`adb.explorer`, `adb.collector`, `adb.utils`, `adb.display`, `adb.infra.query`, etc.).

## [2026-03-25] - refactor/align-philosophy

Reestruturacao para alinhar a lib com sua identidade de
"unified data access layer for Brazilian economic data".

### Added

- **API stateless `fetch()`**: novo metodo em todos os explorers que busca
  dados direto da API sem tocar em disco.
- **Template method `BaseCollector.collect()`**: loop normalize -> start -> iterate -> end
  vive na base, eliminando duplicacao nos 5 collectors.
- **`status()` automatico**: BaseCollector deriva subdirs do `_CONFIG` automaticamente.

### Removed

- **Provider CAGED/MTE**: microdados sao dominio diferente de series temporais.
- **Schemas Pydantic**: dead code nunca chamado.
- **`QueryEngine` e `DataManager` do top-level exports**: infra interna nao e API publica.
