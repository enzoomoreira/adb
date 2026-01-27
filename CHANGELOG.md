# Project Changelog

## [2026-01-27 19:20]

### Added
- Novo modulo `core/display.py` para gerenciamento de output visual ao usuario
  - Classe `Display` com suporte a cores ANSI (auto-detecta TTY e habilita VIRTUAL_TERMINAL_PROCESSING no Windows)
  - Wrapper `_ProgressBar` integrado com tqdm, notifica Display para usar `tqdm.write()` automaticamente
  - Singleton thread-safe com double-checked locking via `get_display()`
  - Metodos para banners, status de fetch, warnings/errors coloridos, e barras de progresso
- Context manager `_capture_external_output()` no Bloomberg client para capturar stdout/stderr do SDK xbbg e redirecionar para arquivo de log (mantendo terminal limpo)

### Changed
- Refatorado sistema de logging para separar concerns:
  - `core/log.py`: Agora gera apenas logs tecnicos em arquivo (removido console handler)
  - `core/display.py`: Responsavel por todo output visual ao usuario
- `BaseCollector` agora usa Display singleton para output visual e Logger para arquivo
  - `_log_fetch_start/result`: Exibem no console via Display + log tecnico em arquivo
  - `_log_collect_start/end`: Banners visuais separados de logs tecnicos
  - Novos metodos `_log_info()` e `_log_warning()` com mesma separacao
- Atualizado `BloombergClient` para capturar mensagens de debug do xbbg
- Simplificada API publica - acesso unificado via explorers:
  ```python
  import adb
  adb.sgs.collect()                    # Coleta
  adb.sgs.read('selic', start='2020')  # Leitura
  adb.sgs.available()                  # Lista indicadores
  adb.sgs.info('selic')                # Detalhes
  ```
- Atualizadas documentacoes em `docs/` para refletir nova arquitetura

### Removed
- Parametro `verbose` removido de `get_logger()` (agora apenas arquivo)
- Console handler removido do modulo de logging (substituido por Display)
- Exports de configuracao removidos dos `__init__.py` (9 modulos):
  - `bacen`: `SGS_CONFIG`, `EXPECTATIONS_CONFIG`
  - `bacen/sgs`: `SGS_CONFIG`
  - `bacen/expectations`: `EXPECTATIONS_CONFIG`
  - `mte`: `CAGED_CONFIG`
  - `mte/caged`: `CAGED_CONFIG`
  - `ibge`: `SIDRA_CONFIG`
  - `ibge/sidra`: `SIDRA_CONFIG`, `SidraCollector`
  - `ipea`: `IPEA_CONFIG`
  - `bloomberg`: `BLOOMBERG_CONFIG`
- Funcoes auxiliares removidas de `core/__init__.py`:
  - `list_indicators()`, `get_indicator_config()`, `filter_by_field()` (usar explorers)
