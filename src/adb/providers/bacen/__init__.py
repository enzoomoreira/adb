"""
Modulo BACEN (interno) - Dados do Banco Central do Brasil.

Contem:
- sgs: Series temporais SGS
- expectations: Expectativas Focus

Uso via API publica:
    import adb
    adb.sgs.collect()
    adb.sgs.read('selic')
    adb.expectations.collect()
    adb.expectations.read('ipca_anual')
"""
