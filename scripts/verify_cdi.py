"""
Script para verificar como os dados do CDI vem da API e calcular a anualizacao.

Uso: uv run scripts/verify_cdi.py
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd


def load_parquet(name: str) -> pd.DataFrame:
    """Carrega parquet do diretorio raw/sgs/daily."""
    parquet_path = Path(__file__).parent.parent / "data" / "raw" / "sgs" / "daily" / f"{name}.parquet"
    if not parquet_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(parquet_path)


def load_parquet_cdi():
    """Carrega dados do CDI do parquet local."""
    print("=" * 70)
    print("1. DADOS DO PARQUET LOCAL - CDI")
    print("=" * 70)

    df = load_parquet("cdi")
    if df.empty:
        print("Arquivo nao encontrado!")
        return None

    print(f"\nShape: {df.shape}")
    print(f"Colunas: {df.columns.tolist()}")
    print(f"Tipo do indice: {type(df.index)}")
    print(f"Periodo: {df.index.min()} a {df.index.max()}")
    print(f"\nUltimos 10 registros:\n{df.tail(10)}")

    # Identificar coluna de valor
    value_col = 'value' if 'value' in df.columns else df.columns[0]
    print(f"\nEstatisticas da coluna '{value_col}':")
    print(f"  Min: {df[value_col].min():.6f}")
    print(f"  Max: {df[value_col].max():.6f}")
    print(f"  Media: {df[value_col].mean():.6f}")

    return df


def calculate_annualized(daily_rate):
    """
    Calcula taxa anualizada a partir da taxa diaria.

    Formula: (1 + taxa_diaria/100)^252 - 1

    O CDI vem em percentual (ex: 0.055 significa 0.055% ao dia)
    Precisamos dividir por 100 para converter para decimal antes de anualizar.
    """
    return ((1 + daily_rate / 100) ** 252 - 1) * 100


def compare_with_selic():
    """Compara CDI com SELIC usando dados locais."""
    print("\n" + "=" * 70)
    print("2. COMPARACAO CDI vs SELIC (dados locais)")
    print("=" * 70)

    cdi_df = load_parquet("cdi")
    selic_df = load_parquet("selic")

    if cdi_df.empty or selic_df.empty:
        print("Arquivos nao encontrados!")
        return None

    # Renomear colunas
    cdi_df = cdi_df.rename(columns={'value': 'cdi'})
    selic_df = selic_df.rename(columns={'value': 'selic'})

    # Juntar por indice
    df = cdi_df.join(selic_df, how='inner')

    # Calcular CDI anualizado
    df['cdi_anualizado'] = calculate_annualized(df['cdi'])

    print("\nComparacao (SELIC ja vem anualizada, CDI diario):")
    print(f"\nUltimos 15 registros:")
    print(df[['cdi', 'cdi_anualizado', 'selic']].tail(15).to_string())

    print("\n\nDiferenca cdi_anualizado - selic (ultimos 30 dias):")
    recent = df.tail(30)
    diff = recent['cdi_anualizado'] - recent['selic']
    print(f"  Media: {diff.mean():.4f} p.p.")
    print(f"  Min: {diff.min():.4f} p.p.")
    print(f"  Max: {diff.max():.4f} p.p.")

    return df


def demonstrate_formula():
    """Demonstra a formula de anualizacao com exemplo."""
    print("\n" + "=" * 70)
    print("4. DEMONSTRACAO DA FORMULA")
    print("=" * 70)

    # Exemplo com CDI de 0.0421% ao dia (tipico quando SELIC = 10.5%)
    cdi_diario = 0.0421

    print(f"\nExemplo: CDI diario = {cdi_diario}%")
    print(f"\nFormula: (1 + taxa_diaria/100)^252 - 1")
    print(f"       = (1 + {cdi_diario}/100)^252 - 1")
    print(f"       = (1 + {cdi_diario/100:.6f})^252 - 1")
    print(f"       = ({1 + cdi_diario/100:.6f})^252 - 1")
    print(f"       = {(1 + cdi_diario/100)**252:.6f} - 1")
    print(f"       = {((1 + cdi_diario/100)**252 - 1):.6f}")
    print(f"       = {((1 + cdi_diario/100)**252 - 1) * 100:.2f}% ao ano")


def main():
    print("\n" + "=" * 70)
    print("VERIFICACAO DOS DADOS DO CDI")
    print("=" * 70)

    # 1. Verificar parquet local
    parquet_df = load_parquet_cdi()

    # 2. Comparar com SELIC
    comparison_df = compare_with_selic()

    # 3. Demonstrar formula com valor real
    demonstrate_formula()

    # 4. Demonstrar com valor atual
    if parquet_df is not None:
        print("\n" + "=" * 70)
        print("4. CALCULO COM VALOR ATUAL")
        print("=" * 70)
        current_cdi = parquet_df['value'].iloc[-1]
        annualized = calculate_annualized(current_cdi)
        print(f"\nCDI diario atual: {current_cdi:.6f}%")
        print(f"CDI anualizado:   {annualized:.2f}%")

    print("\n" + "=" * 70)
    print("CONCLUSAO")
    print("=" * 70)
    print("""
O CDI vem como taxa percentual DIARIA (ex: 0.055% ao dia).
Para plotar junto com a SELIC (que ja vem anualizada), usar:

    cdi_anualizado = ((1 + cdi_diario/100) ** 252 - 1) * 100

Recomendacao: Adicionar coluna 'cdi_anualizado' no consolidate()
do SGSCollector para o arquivo sgs_daily_consolidated.parquet.
""")


if __name__ == "__main__":
    main()
