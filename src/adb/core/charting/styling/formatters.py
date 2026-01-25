from matplotlib.ticker import FuncFormatter, MaxNLocator
import pandas as pd

def currency_formatter(currency: str = 'BRL'):
    """Formatador para valores monetarios (R$ 1.000,00)."""
    def _format(x, pos):
        if currency == 'BRL':
            return f'R$ {x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        elif currency == 'USD':
            return f'$ {x:,.2f}'
        return f'{x:,.2f}'
    return FuncFormatter(_format)

def percent_formatter(decimals: int = 1):
    """Formatador para porcentagens (10,5%)."""
    def _format(x, pos):
        return f'{x:.{decimals}f}%'.replace('.', ',')
    return FuncFormatter(_format)

def human_readable_formatter(decimals: int = 1):
    """Formatador para grandes numeros (1k, 1M, 1B)."""
    def _format(x, pos):
        if x == 0: return "0"
        
        magnitude = 0
        while abs(x) >= 1000:
            magnitude += 1
            x /= 1000.0
            
        suffix = ['', 'k', 'M', 'B', 'T'][magnitude]
        # Remove decimais se for inteiro (ex: 10k e nao 10.0k)
        if x.is_integer():
            return f'{int(x)}{suffix}'
            
        return f'{x:.{decimals}f}{suffix}'.replace('.', ',')
    return FuncFormatter(_format)

