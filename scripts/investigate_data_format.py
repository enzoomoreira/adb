"""Script para investigar duplicacao nos dados coletados."""

from pathlib import Path
import sys
import pandas as pd

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

data_path = Path(__file__).parent.parent / 'data'

print("=" * 70)
print("INVESTIGANDO DUPLICACAO NOS DADOS")
print("=" * 70)

# Verificar IBC-Br (mensal)
print("\n[1] IBC-Br Bruto (sgs/monthly)")
ibc_path = data_path / 'raw' / 'sgs' / 'monthly' / 'ibc_br_bruto.parquet'
if ibc_path.exists():
    df = pd.read_parquet(ibc_path)
    print(f"  Total registros: {len(df)}")
    print(f"  Indice unico: {df.index.is_unique}")
    print(f"  Ultima data: {df.index.max()}")
    print(f"  Ultimos 5 registros:")
    print(df.tail(5))

    # Verificar duplicatas no indice
    duplicados = df.index[df.index.duplicated()]
    if len(duplicados) > 0:
        print(f"\n  ATENCAO: {len(duplicados)} datas duplicadas!")
        print(f"  Datas: {duplicados.tolist()}")
else:
    print("  Arquivo nao existe")

# Verificar IBC-Br Dessaz (mensal)
print("\n[2] IBC-Br Dessazonalizado (sgs/monthly)")
ibc_dessaz_path = data_path / 'raw' / 'sgs' / 'monthly' / 'ibc_br_dessaz.parquet'
if ibc_dessaz_path.exists():
    df = pd.read_parquet(ibc_dessaz_path)
    print(f"  Total registros: {len(df)}")
    print(f"  Indice unico: {df.index.is_unique}")
    print(f"  Ultima data: {df.index.max()}")
    print(f"  Ultimos 5 registros:")
    print(df.tail(5))
else:
    print("  Arquivo nao existe")

# Verificar IGP-M (mensal)
print("\n[3] IGP-M (sgs/monthly)")
igpm_path = data_path / 'raw' / 'sgs' / 'monthly' / 'igp_m.parquet'
if igpm_path.exists():
    df = pd.read_parquet(igpm_path)
    print(f"  Total registros: {len(df)}")
    print(f"  Indice unico: {df.index.is_unique}")
    print(f"  Ultima data: {df.index.max()}")
    print(f"  Ultimos 5 registros:")
    print(df.tail(5))
else:
    print("  Arquivo nao existe")

# Verificar CDI (diario)
print("\n[4] CDI (sgs/daily)")
cdi_path = data_path / 'raw' / 'sgs' / 'daily' / 'cdi.parquet'
if cdi_path.exists():
    df = pd.read_parquet(cdi_path)
    print(f"  Total registros: {len(df)}")
    print(f"  Indice unico: {df.index.is_unique}")
    print(f"  Ultima data: {df.index.max()}")
    print(f"  Ultimos 5 registros:")
    print(df.tail(5))
else:
    print("  Arquivo nao existe")

print("\n" + "=" * 70)
print("TESTANDO LOGICA CORRIGIDA")
print("=" * 70)

from datetime import timedelta

# Simular calculo do start_date para monthly
last_date_ibc = pd.Timestamp('2025-09-01')
last_date_igpm = pd.Timestamp('2025-11-01')

# Logica ANTIGA (errada)
old_start_ibc = (last_date_ibc + timedelta(days=1)).strftime('%Y-%m-%d')
old_start_igpm = (last_date_igpm + timedelta(days=1)).strftime('%Y-%m-%d')

# Logica NOVA (correta)
next_month_ibc = (last_date_ibc.replace(day=1) + timedelta(days=32)).replace(day=1)
next_month_igpm = (last_date_igpm.replace(day=1) + timedelta(days=32)).replace(day=1)
new_start_ibc = next_month_ibc.strftime('%Y-%m-%d')
new_start_igpm = next_month_igpm.strftime('%Y-%m-%d')

print(f"\nIBC-Br (ultima data: {last_date_ibc.date()}):")
print(f"  Logica antiga: buscar desde {old_start_ibc}")
print(f"  Logica nova:   buscar desde {new_start_ibc}")

print(f"\nIGP-M (ultima data: {last_date_igpm.date()}):")
print(f"  Logica antiga: buscar desde {old_start_igpm}")
print(f"  Logica nova:   buscar desde {new_start_igpm}")

# Testar o que a API retorna com a nova logica
from bacen.sgs.client import SGSClient
client = SGSClient()

print(f"\n[5] API com start_date={new_start_ibc} (IBC-Br):")
df_api = client.get_data(
    code=24363,
    name='ibc_br_bruto',
    frequency='monthly',
    start_date=new_start_ibc,
)
if not df_api.empty:
    print(f"  Retornou: {len(df_api)} registros - {df_api.index.tolist()}")
else:
    print("  Sem dados (outubro ainda nao publicado)")

print(f"\n[6] API com start_date={new_start_igpm} (IGP-M):")
df_igpm = client.get_data(
    code=189,
    name='igp_m',
    frequency='monthly',
    start_date=new_start_igpm,
)
if not df_igpm.empty:
    print(f"  Retornou: {len(df_igpm)} registros - {df_igpm.index.tolist()}")
else:
    print("  Sem dados (dezembro ainda nao publicado)")
