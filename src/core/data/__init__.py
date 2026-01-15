"""
Modulo de dados - persistencia e consultas.

Contem:
- DataManager: Persistencia em Parquet (save/read/append/consolidate)
- QueryEngine: Consultas SQL via DuckDB
"""

from .storage import DataManager
from .query import QueryEngine

__all__ = ['DataManager', 'QueryEngine']
