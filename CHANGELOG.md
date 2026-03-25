# Changelog

## [Unreleased] - refactor/align-philosophy

Reestruturacao para alinhar a lib com sua identidade de
"unified data access layer for Brazilian economic data".

### Added

- **API stateless `fetch()`**: novo metodo em todos os explorers que busca
  dados direto da API sem tocar em disco. Permite consumidores como
  projetos internos de database usarem o adb sem cache local.
  ```python
  df = adb.sgs.fetch("selic", start="2020")
  df = adb.sidra.fetch("ipca", start="2024")
  ```
- **`_fetch_one()` extension point** no BaseExplorer: subclasses implementam
  a chamada especifica ao client para habilitar `fetch()`.
- **`_collect_one()` extension point** no BaseCollector: subclasses implementam
  a logica de coleta de um indicador individual.
- **`_subdir_for()` extension point** no BaseCollector: permite derivar subdir
  a partir do config do indicador (ex: SGS daily/monthly).
- **Template method `BaseCollector.collect()`**: loop normalize -> start -> iterate -> end
  vive na base, eliminando duplicacao nos 5 collectors.
- **`status()` automatico**: BaseCollector agora deriva subdirs do `_CONFIG` via
  `_subdir_for()`, eliminando listas hardcoded que podiam divergir do config real.
- Scripts de verificacao em `scripts/` (verify_refactor.py, verify_full.py).

### Removed

- **Provider CAGED/MTE** (`src/adb/providers/mte/`): microdados sao dominio
  diferente de series temporais. Sera lib standalone no futuro. Remove dependencia `py7zr`.
- **Schemas Pydantic** (`domain/schemas/`): 126 linhas de dead code nunca chamado.
  Configs sao dicts fixos no codigo, nao input externo que precise validacao runtime.
- **Funcoes `list_keys()` e `filter_by()`** de shared/utils: zero callers no codebase.
- **`QueryEngine` e `DataManager` do top-level exports**: infra interna nao faz parte
  da API publica. Ainda acessiveis via `from adb.infra.persistence import QueryEngine`.
- Metodos intermediarios `_collect_series()`/`_collect_endpoint()` dos collectors:
  substituidos pelo `_collect_one()` do template method.
- Override de `status()` em SGS/Bloomberg/Sidra collectors: base class resolve.

### Changed

- **Docstring e `__all__` do `__init__.py`**: reflete nova API (fetch como primario,
  5 fontes sem CAGED, sem QueryEngine/DataManager no top-level).
- **`available_sources()`**: retorna 5 fontes (removido "caged").
- **Todos os 5 collectors** simplificados: definem `_CONFIG`, `_TITLE`,
  implementam `_collect_one()` ao inves de override completo de `collect()`.
- Comentarios/docstrings limpos de referencias ao CAGED em arquivos de infra.
- Documentacao completa atualizada (getting-started, extending, querying,
  architecture, domain, services, infra).
