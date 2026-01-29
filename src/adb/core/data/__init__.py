"""
Modulo de dados - persistencia, queries e explorers.

Uso:
    from adb.core.data import sgs, caged, QueryEngine

    # Query pythonica
    df = sgs.read('selic', start='2020')
    df = caged.read(year=2025, uf=35)

    # Query SQL direta
    qe = QueryEngine()
    df = qe.sql("SELECT * FROM '...'")
"""

from .storage import DataManager
from .query import QueryEngine
from .validation import DataValidator, HealthReport, HealthStatus, Frequency, Gap

# Lazy import dos explorers para evitar imports circulares
_sgs = None
_caged = None
_expectations = None
_ipea = None
_bloomberg = None
_sidra = None


def __getattr__(name):
    """Lazy loading dos explorers."""
    global _sgs, _caged, _expectations, _ipea, _bloomberg, _sidra

    if name == 'sgs':
        if _sgs is None:
            from adb.bacen.sgs.explorer import SGSExplorer
            _sgs = SGSExplorer()
        return _sgs

    if name == 'caged':
        if _caged is None:
            from adb.mte.caged.explorer import CAGEDExplorer
            _caged = CAGEDExplorer()
        return _caged

    if name == 'expectations':
        if _expectations is None:
            from adb.bacen.expectations.explorer import ExpectationsExplorer
            _expectations = ExpectationsExplorer()
        return _expectations

    if name == 'ipea':
        if _ipea is None:
            from adb.ipea.explorer import IPEAExplorer
            _ipea = IPEAExplorer()
        return _ipea

    if name == 'bloomberg':
        if _bloomberg is None:
            from adb.bloomberg.explorer import BloombergExplorer
            _bloomberg = BloombergExplorer()
        return _bloomberg

    if name == 'sidra':
        if _sidra is None:
            from adb.ibge.sidra.explorer import SidraExplorer
            _sidra = SidraExplorer()
        return _sidra

    raise AttributeError(f"module 'adb.core.data' has no attribute '{name}'")


__all__ = [
    'DataManager',
    'QueryEngine',
    'DataValidator',
    'HealthReport',
    'HealthStatus',
    'Frequency',
    'Gap',
    'sgs',
    'caged',
    'expectations',
    'ipea',
    'bloomberg',
    'sidra',
]
