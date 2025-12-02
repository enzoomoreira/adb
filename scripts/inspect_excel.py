import pandas as pd

try:
    df = pd.read_excel('BasedeDados_planejamento.xlsx')
    # Filter for BCB related rows
    bcb_df = df[df['Método de Acesso Técnico'].astype(str).str.contains('python-bcb', case=False, na=False) | 
                df['Fonte Recomendada (Primária)'].astype(str).str.contains('BCB', case=False, na=False)]
    
    print("BCB Related Data:")
    for index, row in bcb_df.iterrows():
        print(f"Index: {index}")
        print(f"Indicador: {row['Dado / Indicador']}")
        print(f"Fonte: {row['Fonte Recomendada (Primária)']}")
        print(f"Metodo: {row['Método de Acesso Técnico']}")
        print(f"Obs/Cod: {row['Observação / Código']}")
        print("-" * 20)

except Exception as e:
    print(f"Error reading excel: {e}")
