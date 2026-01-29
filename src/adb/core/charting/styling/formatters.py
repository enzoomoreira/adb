from matplotlib.ticker import FuncFormatter

# Sufixos para notacao compacta de grandes numeros
MAGNITUDE_SUFFIXES = ['', 'k', 'M', 'B', 'T']


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
    """Formatador para porcentagens com separador de milhar (10.000,5%)."""
    def _format(x, pos):
        # Formata com separador de milhar e converte para padrao BR
        return f'{x:,.{decimals}f}%'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return FuncFormatter(_format)

def human_readable_formatter(decimals: int = 1):
    """
    Formatador para grandes numeros (1k, 1M, 1B, 1T).

    Args:
        decimals: Numero de casas decimais (default: 1)

    Returns:
        FuncFormatter para uso com matplotlib
    """
    def _format(x, pos):
        if x == 0:
            return "0"

        magnitude = 0
        # Limita magnitude ao maximo disponivel para evitar IndexError
        while abs(x) >= 1000 and magnitude < len(MAGNITUDE_SUFFIXES) - 1:
            magnitude += 1
            x /= 1000.0

        suffix = MAGNITUDE_SUFFIXES[magnitude]
        # Remove decimais se for inteiro (ex: 10k e nao 10.0k)
        if x == int(x):
            return f'{int(x)}{suffix}'

        return f'{x:.{decimals}f}{suffix}'.replace('.', ',')

    return FuncFormatter(_format)

def points_formatter(decimals: int = 0):
    """
    Formatador para valores numericos com separador de milhar (padrao BR).

    Usado para unidades como pontos de indice, saldo de empregos, etc.
    Exemplo: 1234567 -> 1.234.567
    """
    def _format(x, pos):
        if x == 0:
            return "0"

        # Verifica se o valor e inteiro ou tem decimais significativos
        if decimals == 0 or x == int(x):
            # Formata como inteiro com separador de milhar (padrao BR: ponto)
            return f'{int(x):,}'.replace(',', '.')
        else:
            # Formata com decimais (padrao BR: ponto para milhar, virgula para decimal)
            return f'{x:,.{decimals}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    return FuncFormatter(_format)

