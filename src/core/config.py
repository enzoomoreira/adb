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
