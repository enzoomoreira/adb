"""
Providers - Modulos de coleta e consulta de dados de fontes externas.

Cada provider e um namespace que contem:
- explorer: Interface de leitura e coleta
- collector: Classe de coleta de dados
- client: Cliente HTTP para API
- indicators: Configuracao de indicadores

Providers disponiveis:
- bacen: Banco Central (SGS, Expectations)
- ibge: IBGE (SIDRA)
- ipea: IPEADATA
- bloomberg: Bloomberg Terminal
- mte: Ministerio do Trabalho (CAGED)
"""
