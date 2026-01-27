"""
Configuracao global do projeto.

Resolve DATA_PATH automaticamente baseado na raiz do projeto.
"""

from pathlib import Path


def get_project_root() -> Path:
    """
    Encontra raiz do projeto (onde esta pyproject.toml ou .git).

    Sobe na arvore de diretorios ate encontrar.

    Returns:
        Path para raiz do projeto
    """
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists():
            return parent
        if (parent / '.git').exists():
            return parent
    # Fallback: diretorio atual
    return Path.cwd()


PROJECT_ROOT = get_project_root()
DATA_PATH = PROJECT_ROOT / 'data'
OUTPUTS_PATH = DATA_PATH / 'outputs'
LOG_PATH = PROJECT_ROOT / 'logs'

# =========================================================================
# Resilience defaults (retry, timeout)
# =========================================================================
DEFAULT_REQUEST_TIMEOUT = 30  # segundos
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0  # segundos
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_CHUNK_DELAY = 2.0  # delay entre chunks de requisicao
