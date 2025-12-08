"""
Visualizacao rapida dos dados IPEA.
"""

from pathlib import Path
import pandas as pd

# Carregar dados consolidados
data_path = Path(__file__).parent.parent / "data"
df = pd.read_parquet(data_path / "processed" / "ipea_monthly_consolidated.parquet")

print("=" * 70)
print("DADOS IPEA CONSOLIDADOS")
print("=" * 70)
print(f"\nPeriodo: {df.index.min().strftime('%Y-%m')} a {df.index.max().strftime('%Y-%m')}")
print(f"Registros: {len(df)}")
print(f"Colunas: {list(df.columns)}")

print("\n" + "=" * 70)
print("ULTIMOS 12 MESES")
print("=" * 70)
print(df.tail(12).to_string())

print("\n" + "=" * 70)
print("ESTATISTICAS DESCRITIVAS")
print("=" * 70)
print(df.describe().to_string())

# Saldo CAGED - ultimos 12 meses
print("\n" + "=" * 70)
print("SALDO CAGED - ULTIMOS 12 MESES")
print("=" * 70)
saldo = df["caged_saldo"].dropna().tail(12)
for date, value in saldo.items():
    bar = "#" * int(abs(value) / 20000)
    sign = "+" if value > 0 else ""
    print(f"{date.strftime('%Y-%m')}: {sign}{value:>10,.0f} {bar}")

# Media movel 6 meses
print("\n" + "=" * 70)
print("MEDIA MOVEL 6 MESES - SALDO CAGED")
print("=" * 70)
mm6 = df["caged_saldo"].rolling(6).mean().dropna().tail(6)
for date, value in mm6.items():
    print(f"{date.strftime('%Y-%m')}: {value:>10,.0f}")
