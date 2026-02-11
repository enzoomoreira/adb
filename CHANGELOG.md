# Project Changelog

## [2026-02-11 19:30]

### Fixed
- ExpectationsClient: inicializacao da API OData do BCB agora e lazy (sob demanda), evitando JSONDecodeError quando a API retorna resposta vazia durante o construtor. A inicializacao agora ocorre dentro de metodos protegidos por `@retry`, garantindo resiliencia a falhas transientes

## [2026-02-07 03:09]

### Added
- Indicadores Bloomberg: P/L Ibovespa (`ibov_pl`), DY Ibovespa (`ibov_dy`), IGPM (`igpm`)
- Graficos no report: P/L Ibovespa, DY Ibovespa, IGPM
- `pyrightconfig.json` para integracao Pyright com venv UV
- `CLAUDE.md` com documentacao de erros conhecidos de stubs de terceiros

### Changed
- Bloomberg collector/explorer agora usam subdiretorio dinamico por frequencia (`daily`/`monthly`), alinhado com padrao SGS/Sidra
- `BloombergCollector.get_status()` agora agrega status de `bloomberg/daily` e `bloomberg/monthly`
- Lookback de coleta Bloomberg aumentado de 2 para 6 anos
- Periodo de graficos Bloomberg no report aumentado de 2 para 5 anos
- Titulos de servicos no report ajustados para "Servicos - Volume"

### Fixed
- Type hints corrigidos em 24 arquivos: `param: Type = None` -> `param: Type | None = None` (184 -> 45 erros Pyright, restantes sao stubs de terceiros)
- `get_status()` overrides agora compatíveis com assinatura do `BaseCollector`
- Guards adicionados em `resilience.py` para `retry_state.fn` e `retry_state.outcome` possivelmente None
- Ruff lint: removida variavel morta `has_files`, `except Exception as e` nao utilizado, bare `except` -> `except Exception`

## [2026-02-05 00:21]

### Changed
- **BaseExplorer.read()**: Coluna `value` agora e renomeada para o nome do indicador ao ler um unico indicador (ex: `selic` ao inves de `value`)
- **ExpectationsExplorer.read()**: Mesma convencao de rename aplicada quando `year` ou `smooth` sao usados com indicador unico
- **pnad_desocupacao**: Migrado da tabela SIDRA 4099 (trimestral) para 6381 (trimestre movel com publicacao mensal), refletindo a metodologia correta da PNAD Continua
- **generate_full_report.py**: Referencias de coluna atualizadas de `'value'` para nomes especificos (`'selic_acum_mensal'`, `'ipca_12m'`, `'juros_real'`) conforme nova convencao
- **docs/advanced/extending.md**: Documentacao atualizada para refletir que explorers renomeiam `value` para o nome do indicador no `read()`

## [2026-01-30 15:05]

### Changed
- **generate_full_report.py**: Calculo de juros real agora usa formula inline de Fisher ao inves de `chartkit.real_rate()`:
  - Formula explicita: `((1 + selic_12m/100) / (1 + ipca/100) - 1) * 100`
  - Remove dependencia de funcao externa para calculo simples
- **display.py**: Barra de progresso Rich aprimorada com mais informacoes:
  - Adicionado contador `MofNCompleteColumn` (ex: "15/100")
  - Adicionado tempo decorrido `TimeElapsedColumn` com separador "/"
  - Taxa de refresh aumentada de 10Hz para 15Hz (melhor responsividade)
- **caged/collector.py**: Removido parametro `unit="mes"` da progress bar (deprecated no Rich)

## [2026-01-30 05:16]

### Changed
- **Refatoracao arquitetural completa**: Migracao de estrutura flat por provider para arquitetura em camadas (Clean Architecture):
  - `core/` -> Distribuido entre `domain/`, `infra/`, `services/`, `shared/`
  - `bacen/`, `bloomberg/`, `ibge/`, `ipea/`, `mte/` -> Consolidados em `providers/`

### Added
- Nova camada **domain/** (regras de negocio):
  - `schemas/`: Schemas Pydantic para indicadores (`IndicatorConfig`, etc.)
  - `exceptions.py`: Excecoes do dominio
  - `explorers.py`: Classes base de exploracao de dados
- Nova camada **infra/** (infraestrutura):
  - `config.py`: Configuracoes globais
  - `log.py`: Sistema de logging com loguru
  - `resilience.py`: Retry com tenacity
  - `persistence/`: Storage, query engine e validacao de dados
- Nova camada **providers/** (fontes de dados):
  - `bacen/sgs/`: Client, collector, explorer, indicators
  - `bacen/expectations/`: Client, collector, explorer, indicators
  - `bloomberg/`: Client, collector, explorer, indicators
  - `ibge/sidra/`: Client, collector, explorer, indicators
  - `ipea/`: Client, collector, explorer, indicators
  - `mte/caged/`: Client, collector, explorer, indicators
- Nova camada **services/** (servicos de aplicacao):
  - `collectors/base.py`: BaseCollector
  - `collectors/registry.py`: Registry de collectors
- Nova camada **shared/** (utilitarios):
  - `utils/dates.py`: Funcoes de manipulacao de datas
  - `utils/indicators.py`: Funcoes de indicadores
- Camada **ui/** expandida:
  - `__init__.py` com exports publicos

### Removed
- Estrutura antiga com modulos por provider na raiz de `src/adb/`:
  - `bacen/` (45 arquivos, ~1500 linhas)
  - `bloomberg/` (5 arquivos, ~500 linhas)
  - `ibge/` (6 arquivos, ~900 linhas)
  - `ipea/` (5 arquivos, ~400 linhas)
  - `mte/` (6 arquivos, ~750 linhas)
  - `core/` monolitico (~2000 linhas)
- Total: **~6000 linhas** de codigo legado removidas e reorganizadas

## [2026-01-30 04:25]

### Changed
- Refatoracao arquitetural para **lazy loading** de dependencias pesadas (Rich, loguru):
  - `core/log.py`: Imports de loguru e config movidos para dentro de `_ensure_configured()` (lazy)
  - `core/data/query.py`: Logger agora e carregado sob demanda via `_get_logger()`
  - `core/resilience.py`: Logger agora e carregado sob demanda via `_get_logger()`
  - `core/collectors/base.py`: Imports de `display` e `log` movidos para dentro do `__init__`
  - `core/__init__.py`: Display e get_display agora usam `__getattr__` para lazy loading
- `core/data/storage.py` refatorado com **Callback Pattern** para desacoplar de display:
  - `StorageCallback`: Protocol para feedback de operacoes
  - `NullCallback`: Implementacao silenciosa (default)
  - `DisplayCallback`: Adapter que conecta ao display Rich
  - `DataManager` agora aceita `callback` opcional no construtor

### Added
- Novo modulo `ui/` para separacao de responsabilidades:
  - `display.py` movido de `core/` para `ui/`
  - `ui/__init__.py` com exports publicos
- Alias de compatibilidade em `core/display.py` (deprecated, emite warning)

### Performance
- `import adb` agora **nao carrega Rich** (~90ms economizados no import time)
- Display e carregado apenas quando um collector e instanciado ou display e explicitamente usado
- `adb.sgs.available()` funciona sem carregar display

## [2026-01-30 01:57]

### Added
- Novo modulo `core/schemas/` com validacao Pydantic para configuracoes de indicadores:
  - `IndicatorConfig`: Schema base com campos comuns (name, frequency, description)
  - `SGSIndicatorConfig`: Valida codigo SGS (int > 0)
  - `IPEAIndicatorConfig`: Valida codigo IPEA (string nao-vazia) com unit/source opcionais
  - `SIDRAIndicatorConfig`: Valida tabela SIDRA com parametros obrigatorios
  - `validate_indicator_config()`: Funcao para validar dicionarios de configuracao
- Schemas exportados em `core/__init__.py` para facil acesso
- Dependencias: `pydantic>=2.12.5`, `loguru>=0.7.3`, `rich>=14.3.1`, `tenacity>=9.1.2`

### Changed
- Modulo `core/display.py` reescrito para usar **Rich** ao inves de tqdm:
  - `_ProgressBar` agora usa `rich.progress.Progress` com spinner, barra e tempo restante
  - Detecta automaticamente ambiente Jupyter e desativa HTML rendering (evita duplicacao de outputs)
  - Banners agora usam `rich.panel.Panel` com bordas coloridas
  - Mensagens de fetch/status usam markup Rich para cores
  - Removida classe `_Colors` (cores ANSI manuais) - Rich gerencia automaticamente
  - Parametro `unit` de `progress()` esta deprecated (nao usado pelo Rich Progress)
- Modulo `core/log.py` reescrito para usar **loguru**:
  - Lazy initialization via `_configure_logger()` (configura apenas na primeira chamada)
  - Retencao de logs aumentada para 30 dias
  - `get_logger()` retorna `logger.bind(name=name)` para contexto
- Modulo `core/resilience.py` reescrito para usar **tenacity**:
  - Decorator `retry()` agora e wrapper do `tenacity.retry`
  - Callbacks `_before_sleep_log` e `_log_final_failure` para logging com loguru
  - Suporta jitter via `wait_random_exponential` ou backoff fixo via `wait_exponential`

### Removed
- Dependencia `tqdm` removida (substituida por Rich)

## [2026-01-30 00:50]

### Removed
- Modulo `core/charting/` completamente removido do projeto:
  - Accessor `df.agora.plot()` (accessor.py)
  - Motor de plotagem `AgoraPlotter` (engine.py)
  - Sistema de overlays (moving_average, bands, reference_lines)
  - Componentes (footer, markers, collision detection)
  - Tema e paleta de cores (styling/)
  - Transformacoes (yoy, mom, accum_12m, annualize_daily, compound_rolling, real_rate, etc.)
  - Fonte BradescoSans-Light.ttf
- Documentacao `docs/charting.md` removida
- Dependencias `matplotlib` e `statsmodels` removidas do pyproject.toml
- Atributo `adb.charting` removido (lazy loading)

### Changed
- Visualizacao agora usa biblioteca externa **chartkit** (instalada localmente via path editable)
- Script `generate_full_report.py` atualizado para usar `chartkit` ao inves de `adb.core.charting`:
  - `df.agora.plot()` -> `df.chartkit.plot()`
  - `charting.to_month_end()` -> `chartkit.to_month_end()`
  - `charting.compound_rolling()` -> `chartkit.compound_rolling()`
  - `charting.real_rate()` -> `chartkit.real_rate()`
- Documentacoes atualizadas para referenciar chartkit:
  - `README.md`: Nova secao "Visualizacao (chartkit)" com exemplo de uso
  - `docs/architecture.md`: Diagramas atualizados, referencias ao chartkit externo
  - `docs/core.md`: Removida secao charting, adicionada nota sobre chartkit
- `.gitignore` atualizado: adicionada pasta `assets/`

### Added
- Arquivo `charting.toml` (nao rastreado) com configuracao de charting

## [2026-01-29 15:56]

### Added
- Sistema de overlays para graficos:
  - Media movel (`moving_avg` parameter)
  - Linhas ATH/ATL (`show_ath`, `show_atl`)
  - Linhas horizontais customizadas (`overlays['hlines']`)
  - Bandas sombreadas (`overlays['band']`)
- Novo modulo `core/charting/overlays/` com funcoes: `add_moving_average`, `add_ath_line`, `add_atl_line`, `add_hline`, `add_band`
- Novo modulo `core/charting/components/collision.py` para resolucao de colisoes entre labels
- Funcao `highlight_last_bar()` para destacar ultimo valor em graficos de barra
- Novas transformacoes em `charting/transforms.py`:
  - `annualize_daily()`: Anualiza taxa diaria usando juros compostos
  - `compound_rolling()`: Calcula retorno composto em janela movel (ex: Selic 12m)
  - `real_rate()`: Calcula juros real via Equacao de Fisher
  - `to_month_end()`: Normaliza indice temporal para fim do mes
- Formatador `points_formatter()` para valores numericos com separador de milhar BR
- Graficos de juros real, CAGED saldo, e 9 indicadores Bloomberg no script de relatorio

### Changed
- `AgoraAccessor.plot()` agora aceita parametros de overlay: `moving_avg`, `show_ath`, `show_atl`, `overlays`
- `AgoraPlotter.plot()` aplica formatter do eixo Y antes da plotagem (corrige highlight_last)
- `plot_bar()` agora suporta `highlight=True` para destacar ultima barra
- Mapa de formatadores `_FORMATTERS` extraido para facilitar extensao
- `percent_formatter()` agora inclui separador de milhar para valores grandes
- `human_readable_formatter()` protegido contra IndexError em magnitudes extremas
- Script `generate_full_report.py` refatorado:
  - Filtro de periodo via `get_start_date()` ao inves de parametro `years`
  - Adicionados graficos de Bloomberg, IPEA e juros real
- Frequencia de `selic_acum_mensal` corrigida de 'daily' para 'monthly' em indicators.py
- `.gitignore` atualizado para ignorar pasta `.claude/`

### Removed
- Metodo `_validate()` do `AgoraAccessor` (nao fazia nada)
- Parametro `years` removido de `save_chart()` (filtro agora e feito na leitura)

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
