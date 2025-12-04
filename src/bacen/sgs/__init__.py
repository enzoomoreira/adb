from .client import SGSClient
from .collector import SGSCollector
from .indicators import (
    INDICATORS,
    get_by_frequency,
    get_codes_dict,
    get_indicator_keys,
    get_indicator_config,
    list_indicators,
    # Compatibilidade com formato antigo
    IBC_BR,
    IGP_M,
    SELIC,
    CURRENCY,
    CDI,
    MONTHLY_INDICATORS,
    DAILY_INDICATORS,
    ALL_SGS_CODES,
)

__all__ = [
    # Principais
    'SGSClient',
    'SGSCollector',
    'INDICATORS',
    # Helpers
    'get_by_frequency',
    'get_codes_dict',
    'get_indicator_keys',
    'get_indicator_config',
    'list_indicators',
    # Compatibilidade
    'IBC_BR',
    'IGP_M',
    'SELIC',
    'CURRENCY',
    'CDI',
    'MONTHLY_INDICATORS',
    'DAILY_INDICATORS',
    'ALL_SGS_CODES',
]
