# Project Changelog

## [2026-01-29 04:13]

### Added
- Novo modulo `core/data/validation.py` para validacao de integridade de dados:
  - Classe `DataValidator` com context manager para analise de saude dos dados
  - `HealthReport` dataclass com metricas: cobertura, gaps, staleness, resultados cuallee
  - `HealthStatus` enum: OK, STALE, GAPS, MISSING
  - Usa calendario ANBIMA (bizdays) para calcular dias uteis brasileiros
  - Usa cuallee para checks de qualidade (is_complete, is_unique na coluna date)
- Novo indicador SGS `selic_acum_mensal` (codigo 4390) - Taxa Selic acumulada no mes
- Dependencias: `bizdays>=1.0.14`, `cuallee[duckdb]>=0.5.2`

### Changed
- `BaseCollector.get_status()` agora usa DataValidator para calcular metricas de saude:
  - Retorna cobertura percentual, contagem de gaps e status real (OK/STALE/GAPS/MISSING)
  - Subclasses devem implementar `_get_frequency_for_file()` para lookup de frequencia
- `BaseCollector._sync()` refatorado para usar health check antes de coletar:
  - Valida dados existentes com DataValidator
  - Determina estrategia de coleta baseada no status de saude
- `BaseCollector._next_date()` agora suporta frequencia 'quarterly'
- Collectors refatorados para implementar `_get_frequency_for_file()`:
  - `SGSCollector`, `SidraCollector`, `IPEACollector`, `BloombergCollector`
- `BloombergCollector.collect()` agora passa `subdir` e `check_first_run` para `_start()`
- `DataManager.append()`: UNION ALL alterado para UNION ALL BY NAME (casa colunas por nome, evita erro de tipo)
- `BaseExplorer._join()`: Simplificado usando `pd.concat(axis=1)` ao inves de loop com join
- `plot_line()`: Removida conversao para numpy - matplotlib 3.0+ aceita pandas diretamente

## [2026-01-27 20:22]

### Changed
- Renomeados metodos internos do `BaseCollector` para nomes mais concisos:
  - `_normalize_indicators_list()` -> `_normalize_indicators()`
  - `_calculate_start_date()` -> `_next_date()`
  - `_collect_with_sync()` -> `_sync()`
  - `_log_collect_start()` -> `_start()`
  - `_log_collect_end()` -> `_end()`
  - `_log_fetch_start()` -> `_fetch_start()`
  - `_log_fetch_result()` -> `_fetch_result()`
  - `_log_info()` -> `_info()`
  - `_log_warning()` -> `_warning()`
- Renomeados metodos internos do `BaseExplorer`:
  - `_get_subdir()` -> `_subdir()`
  - `_build_where()` -> `_where()`
  - `_join_multiple()` -> `_join()`
- Renomeados metodos internos do `QueryEngine`:
  - `_ensure_date_columns()` -> `_ensure_dates()`
  - `_build_query()` -> `_query()`
- Renomeadas funcoes utilitarias em `core/utils/`:
  - `normalize_date_index()` -> `normalize_index()`
  - `get_indicator_config()` -> `get_config()`
  - `list_indicators()` -> `list_keys()`
  - `filter_by_field()` -> `filter_by()`
- `BaseCollector._end()` agora usa total de registros acumulado automaticamente via `_fetch_result()` (removido parametro `results`)
- Atualizadas documentacoes `docs/bacen.md` e `docs/core.md` para refletir novos nomes

### Removed
- Metodos wrapper removidos do `ExpectationsClient` (usar `query()` diretamente):
  - `get_selic_expectations()`
  - `get_annual_expectations()`
  - `get_inflation_expectations()`
  - `get_monthly_expectations()`
- Metodos wrapper removidos do `SGSClient`:
  - `query()` (alias para `get_series()`)
  - `get_single_series()` (usar `get_series({name: code})`)

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
