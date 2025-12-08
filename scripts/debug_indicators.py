from bcb import Expectativas
import pandas as pd


def check_indicators(endpoint_name):
    print(f"\nChecking endpoint: {endpoint_name}")
    try:
        em = Expectativas()
        ep = em.get_endpoint(endpoint_name)

        # Query distinct indicators if possible, or just fetch a sample
        # Fetching recent data to see what indicators are active
        df = ep.query().limit(1000).collect()

        if df.empty:
            print("  No data returned.")
            return

        if "Indicador" in df.columns:
            unique_indicators = df["Indicador"].unique()
            print(f"  Available indicators ({len(unique_indicators)}):")
            for ind in sorted(unique_indicators):
                print(f"    - '{ind}'")
        else:
            print(f"  Column 'Indicador' not found. Columns: {df.columns.tolist()}")

    except Exception as e:
        print(f"  Error: {e}")


if __name__ == "__main__":
    check_indicators("ExpectativasMercadoTop5Anuais")
    check_indicators("ExpectativaMercadoMensais")
    check_indicators("ExpectativasMercadoAnuais")
