"""
Script de exploracao da API de Expectativas do BCB (Relatorio Focus).

Objetivo: Entender a estrutura dos dados retornados por cada endpoint
antes de finalizar o modulo src/bacen/expectations.

Documentacao: https://wilsonfreitas.github.io/python-bcb/expectativas.html
"""

from bcb import Expectativas
import pandas as pd
from pathlib import Path


def print_separator(title: str = ""):
    """Imprime separador visual."""
    print()
    print("=" * 80)
    if title:
        print(f" {title}")
        print("=" * 80)
    print()


def explore_endpoint(em: Expectativas, endpoint_name: str, limit: int = 10):
    """
    Explora um endpoint e retorna informacoes sobre sua estrutura.

    Args:
        em: Objeto Expectativas
        endpoint_name: Nome do endpoint
        limit: Numero de registros para amostra

    Returns:
        DataFrame com amostra dos dados
    """
    print(f"Endpoint: {endpoint_name}")
    print("-" * 60)

    try:
        ep = em.get_endpoint(endpoint_name)
        df = ep.query().limit(limit).collect()

        if df.empty:
            print("  [VAZIO] Nenhum dado retornado")
            return df

        print(f"  Registros: {len(df)}")
        print(f"  Colunas ({len(df.columns)}):")
        for col in df.columns:
            dtype = df[col].dtype
            sample = df[col].iloc[0] if len(df) > 0 else "N/A"
            # Truncar valores longos
            sample_str = str(sample)[:40]
            print(f"    - {col}: {dtype} (ex: {sample_str})")

        # Mostrar indicadores unicos se existir coluna Indicador
        if 'Indicador' in df.columns:
            # Buscar mais dados para ver todos indicadores
            df_full = ep.query().limit(1000).collect()
            indicadores = df_full['Indicador'].unique()
            print(f"  Indicadores disponiveis ({len(indicadores)}):")
            for ind in sorted(indicadores):
                print(f"    - {ind}")

        return df

    except Exception as e:
        print(f"  [ERRO] {e}")
        return pd.DataFrame()


def test_queries(em: Expectativas):
    """Testa diferentes tipos de queries."""

    print_separator("TESTES DE QUERY")

    # Teste 1: Filtro por indicador
    print("Teste 1: Filtro por indicador (IPCA)")
    print("-" * 60)
    try:
        ep = em.get_endpoint('ExpectativasMercadoTop5Anuais')
        df = (ep.query()
              .filter(ep.Indicador == 'IPCA')
              .limit(5)
              .collect())
        print(f"  Registros: {len(df)}")
        print(df[['Indicador', 'Data', 'DataReferencia', 'Media', 'Mediana']].to_string())
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # Teste 2: Filtro por data
    print("Teste 2: Filtro por data (>= 2024-01-01)")
    print("-" * 60)
    try:
        ep = em.get_endpoint('ExpectativasMercadoTop5Anuais')
        df = (ep.query()
              .filter(ep.Data >= '2024-01-01')
              .filter(ep.Indicador == 'IPCA')
              .limit(5)
              .collect())
        print(f"  Registros: {len(df)}")
        if not df.empty:
            print(df[['Indicador', 'Data', 'DataReferencia', 'Media']].to_string())
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # Teste 3: Select de colunas especificas
    print("Teste 3: Select de colunas especificas")
    print("-" * 60)
    try:
        ep = em.get_endpoint('ExpectativasMercadoTop5Anuais')
        df = (ep.query()
              .filter(ep.Indicador == 'IPCA')
              .select(ep.Data, ep.Media, ep.Mediana)
              .limit(5)
              .collect())
        print(f"  Colunas retornadas: {list(df.columns)}")
        print(df.to_string())
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # Teste 4: OrderBy
    print("Teste 4: OrderBy descendente por Data")
    print("-" * 60)
    try:
        ep = em.get_endpoint('ExpectativasMercadoTop5Anuais')
        df = (ep.query()
              .filter(ep.Indicador == 'IPCA')
              .orderby(ep.Data.desc())
              .limit(5)
              .collect())
        print(f"  Datas (mais recentes primeiro): {df['Data'].tolist()}")
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # Teste 5: Endpoint Selic (estrutura diferente)
    print("Teste 5: Endpoint Selic (estrutura especifica)")
    print("-" * 60)
    try:
        ep = em.get_endpoint('ExpectativasMercadoSelic')
        df = ep.query().limit(5).collect()
        print(f"  Colunas: {list(df.columns)}")
        print(df.to_string())
    except Exception as e:
        print(f"  [ERRO] {e}")

    print()

    # Teste 6: Endpoint Inflacao 12 meses
    print("Teste 6: Endpoint Inflacao 12 meses")
    print("-" * 60)
    try:
        ep = em.get_endpoint('ExpectativasMercadoInflacao12Meses')
        df = ep.query().limit(5).collect()
        print(f"  Colunas: {list(df.columns)}")
        if not df.empty and 'Indicador' in df.columns:
            print(f"  Indicadores: {df['Indicador'].unique().tolist()}")
        print(df.to_string())
    except Exception as e:
        print(f"  [ERRO] {e}")


def save_samples(em: Expectativas, output_dir: Path):
    """Salva amostras de cada endpoint em CSV."""

    print_separator("SALVANDO AMOSTRAS")

    output_dir.mkdir(parents=True, exist_ok=True)

    endpoints = [
        'ExpectativasMercadoTop5Anuais',
        'ExpectativasMercadoAnuais',
        'ExpectativaMercadoMensais',
        'ExpectativasMercadoTrimestrais',
        'ExpectativasMercadoSelic',
        'ExpectativasMercadoTop5Selic',
        'ExpectativasMercadoInflacao12Meses',
        'ExpectativasMercadoInflacao24Meses',
        'ExpectativasMercadoTop5Mensais',
    ]

    for endpoint_name in endpoints:
        try:
            ep = em.get_endpoint(endpoint_name)
            df = ep.query().limit(100).collect()

            if not df.empty:
                filename = f"{endpoint_name.lower()}.csv"
                filepath = output_dir / filename
                df.to_csv(filepath, index=False)
                print(f"  Salvo: {filename} ({len(df)} registros)")
            else:
                print(f"  [VAZIO] {endpoint_name}")

        except Exception as e:
            print(f"  [ERRO] {endpoint_name}: {e}")


def main():
    """Funcao principal."""

    print_separator("EXPLORACAO DA API DE EXPECTATIVAS DO BCB")

    # Inicializar
    print("Inicializando conexao com API...")
    em = Expectativas()

    # Listar endpoints disponiveis
    print_separator("ENDPOINTS DISPONIVEIS")
    try:
        endpoints_info = em.describe()
        print(endpoints_info)
    except Exception as e:
        print(f"Erro ao listar endpoints: {e}")

    # Lista de endpoints para explorar
    endpoints = [
        'ExpectativasMercadoTop5Anuais',
        'ExpectativasMercadoAnuais',
        'ExpectativaMercadoMensais',
        'ExpectativasMercadoTrimestrais',
        'ExpectativasMercadoSelic',
        'ExpectativasMercadoTop5Selic',
        'ExpectativasMercadoInflacao12Meses',
        'ExpectativasMercadoInflacao24Meses',
        'ExpectativasMercadoTop5Mensais',
    ]

    # Explorar cada endpoint
    print_separator("EXPLORANDO ENDPOINTS")

    for endpoint_name in endpoints:
        explore_endpoint(em, endpoint_name, limit=10)
        print()

    # Testes de query
    test_queries(em)

    # Salvar amostras
    output_dir = Path(__file__).parent.parent / 'data' / 'exploration'
    save_samples(em, output_dir)

    print_separator("EXPLORACAO CONCLUIDA")
    print(f"Amostras salvas em: {output_dir}")


if __name__ == '__main__':
    main()
