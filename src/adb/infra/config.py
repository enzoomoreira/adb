"""
Configuracao centralizada da biblioteca.

Paths resolvidos via platformdirs (cache do OS).
Override via variavel de ambiente ADB_DATA_DIR.
"""

from pathlib import Path

from platformdirs import user_cache_dir
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_NAME = "py-adb"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ADB_")

    data_dir: Path = Path(user_cache_dir(APP_NAME, appauthor=False))

    @property
    def data_path(self) -> Path:
        return self.data_dir

    @property
    def logs_path(self) -> Path:
        path = self.data_dir.parent / "Logs"
        path.mkdir(parents=True, exist_ok=True)
        return path


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# =========================================================================
# Resilience defaults (retry, timeout)
# =========================================================================
DEFAULT_REQUEST_TIMEOUT = 30  # segundos
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0  # segundos
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_CHUNK_DELAY = 2.0  # delay entre chunks de requisicao
