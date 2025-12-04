"""
Debug script para investigar comportamento do loop de download.

Hipotese: O loop esta parando/pulando chunks por algum motivo.
Este script simula exatamente o comportamento do notebook para identificar o bug.
"""

from bcb import sgs
import pandas as pd
from datetime import datetime
import traceback

print("=" * 70)
print("DEBUG: Comportamento do Loop de Download")
print("=" * 70)

# Simular exatamente o codigo do notebook
INDICATORS_CONFIG = {
    'dolar_ptax': {
        'name': 'Dolar PTAX Venda',
        'sgs_code': 10813,
        'frequency': 'daily'
    },
    'euro_ptax': {
        'name': 'Euro PTAX Venda',
        'sgs_code': 21619,
        'frequency': 'daily'
    },
    'selic': {
        'name': 'Meta Selic',
        'sgs_code': 432,
        'frequency': 'daily'
    },
}


def download_with_debug(indicator_key, config):
    """
    Versao com debug detalhado do download_historical.
    """
    print(f"\n{'='*60}")
    print(f"BAIXANDO: {config['name']} (codigo {config['sgs_code']})")
    print('='*60)

    chunks = []
    current_year = datetime.now().year

    print(f"current_year = {current_year}")
    print(f"range(1980, {current_year + 1}, 10) = {list(range(1980, current_year + 1, 10))}")
    print()

    # Baixar de 10 em 10 anos (de 1980 ate hoje)
    for i, start_year in enumerate(range(1980, current_year + 1, 10)):
        end_year = min(start_year + 9, current_year)
        start_date = f'{start_year}-01-01'
        end_date = f'{end_year}-12-31'

        print(f"[Iteracao {i+1}] Tentando {start_year}-{end_year}...", end=" ")

        try:
            chunk = sgs.get(
                {config['name']: config['sgs_code']},
                start=start_date,
                end=end_date
            )
            if not chunk.empty:
                chunks.append(chunk)
                print(f"OK - {len(chunk):,} registros")
            else:
                print("VAZIO (DataFrame vazio)")
        except Exception as e:
            error_msg = str(e)
            if "Value(s) not found" in error_msg:
                print(f"SEM DADOS (periodo sem registros)")
            else:
                print(f"ERRO: {error_msg[:80]}")
                # Mostrar traceback completo para erros inesperados
                if "10 anos" not in error_msg and "Value(s) not found" not in error_msg:
                    traceback.print_exc()

    print(f"\nTotal de chunks coletados: {len(chunks)}")

    if chunks:
        df = pd.concat(chunks)
        df = df[~df.index.duplicated(keep='last')]
        df = df.sort_index()
        print(f"DataFrame final: {len(df):,} registros")
        print(f"Periodo: {df.index.min()} a {df.index.max()}")
        return df
    else:
        print("Nenhum dado coletado!")
        return pd.DataFrame()


# Executar para cada indicador problematico
for key, config in INDICATORS_CONFIG.items():
    download_with_debug(key, config)


print("\n" + "=" * 70)
print("ANALISE")
print("=" * 70)
print("""
Compare o output acima com o que o notebook produziu.
Se este script baixou mais dados, o problema esta no ambiente do notebook.
Se este script tambem falhou, o problema esta na API ou no codigo.
""")
