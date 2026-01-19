"""
Modulo de dados - persistencia, queries e explorers.

Uso:
    from core.data import sgs, caged, QueryEngine

    # Query pythonica
    df = sgs.read('selic', start='2020')
    df = caged.read(year=2025, uf=35)

    # Query SQL direta
    qe = QueryEngine()
    df = qe.sql("SELECT * FROM '...'")
"""

from .storage import DataManager
from .query import QueryEngine

# Lazy import dos explorers para evitar imports circulares
_sgs = None
_caged = None
_expectations = None
_ipea = None
_bloomberg = None


def __getattr__(name):
    """Lazy loading dos explorers."""
    global _sgs, _caged, _expectations, _ipea, _bloomberg

    if name == 'sgs':
        if _sgs is None:
            from bacen.sgs.explorer import SGSExplorer
            _sgs = SGSExplorer()
        return _sgs

    if name == 'caged':
        if _caged is None:
            from mte.caged.explorer import CAGEDExplorer
            _caged = CAGEDExplorer()
        return _caged

    if name == 'expectations':
        if _expectations is None:
            from bacen.expectations.explorer import ExpectationsExplorer
            _expectations = ExpectationsExplorer()
        return _expectations

    if name == 'ipea':
        if _ipea is None:
            from ipea.explorer import IPEAExplorer
            _ipea = IPEAExplorer()
        return _ipea

    if name == 'bloomberg':
        if _bloomberg is None:
            from bloomberg.explorer import BloombergExplorer
            _bloomberg = BloombergExplorer()
        return _bloomberg

    raise AttributeError(f"module 'core.data' has no attribute '{name}'")


__all__ = [
    'DataManager',
    'QueryEngine',
    'sgs',
    'caged',
    'expectations',
    'ipea',
    'bloomberg',
]
