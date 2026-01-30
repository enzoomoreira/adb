"""
Modulo de persistencia - storage e queries.

Contem:
- storage: DataManager para gerenciar arquivos parquet
- query: QueryEngine para queries SQL via DuckDB
- validation: DataValidator para health checks
"""

from .storage import DataManager, DisplayCallback, NullCallback
from .query import QueryEngine
from .validation import DataValidator, HealthReport, HealthStatus, Frequency, Gap

__all__ = [
    # Storage
    "DataManager",
    "DisplayCallback",
    "NullCallback",
    # Query
    "QueryEngine",
    # Validation
    "DataValidator",
    "HealthReport",
    "HealthStatus",
    "Frequency",
    "Gap",
]
