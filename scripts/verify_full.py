"""
Verificacao completa: collect, read, fetch, e compatibilidade de formatos.

Testa o pipeline inteiro:
1. collect() - escreve em disco
2. read() - le do disco
3. fetch() - busca da API
4. Compara formato read() vs fetch() (devem ser identicos)
5. get_status() funciona
6. available() e info() funcionam
"""

import sys

import pandas as pd


def test_collect_and_read() -> bool:
    """Testa pipeline collect -> read (escrita e leitura de disco)."""
    import adb

    # Coleta incremental do SGS (selic, poucas rows novas se ja tem dados)
    print("  Coletando selic via adb.sgs.collect()...")
    adb.sgs.collect(["selic"], verbose=True)

    # Le do disco
    df = adb.sgs.read("selic", start="2025-01")
    assert not df.empty, "read('selic') vazio apos collect"
    assert "selic" in df.columns, f"Coluna errada: {df.columns.tolist()}"
    assert df.index.name == "date", f"Index name errado: {df.index.name}"
    assert isinstance(df.index, pd.DatetimeIndex), f"Index type: {type(df.index)}"

    print(f"  [OK] collect -> read: {len(df)} registros")
    return True


def test_format_compatibility() -> bool:
    """Compara formato de read() vs fetch() - devem ser identicos."""
    import adb

    df_read = adb.sgs.read("selic", start="2025-01")
    df_fetch = adb.sgs.fetch("selic", start="2025-01")

    if df_read.empty:
        print("  [SKIP] Sem dados locais para comparar")
        return True

    # Mesmas colunas
    assert df_read.columns.tolist() == df_fetch.columns.tolist(), (
        f"Colunas diferentes: read={df_read.columns.tolist()}, fetch={df_fetch.columns.tolist()}"
    )

    # Mesmo tipo de index
    assert type(df_read.index) == type(df_fetch.index), (
        f"Index type: read={type(df_read.index)}, fetch={type(df_fetch.index)}"
    )

    # Mesmo nome de index
    assert df_read.index.name == df_fetch.index.name, (
        f"Index name: read={df_read.index.name}, fetch={df_fetch.index.name}"
    )

    # Valores proximos (podem diferir minimamente por timing de coleta)
    common_dates = df_read.index.intersection(df_fetch.index)
    if len(common_dates) > 0:
        read_vals = df_read.loc[common_dates, "selic"]
        fetch_vals = df_fetch.loc[common_dates, "selic"]
        assert (read_vals == fetch_vals).all(), "Valores divergem entre read e fetch"

    print(f"  [OK] Formato identico: {len(common_dates)} datas em comum, valores batem")
    return True


def test_collect_sidra() -> bool:
    """Testa collect do SIDRA (outra fonte, confirma que pipeline generico funciona)."""
    import adb

    print("  Coletando ipca via adb.sidra.collect()...")
    adb.sidra.collect(["ipca"], verbose=True)

    df = adb.sidra.read("ipca", start="2024")
    assert not df.empty, "read('ipca') vazio apos collect"
    print(f"  [OK] collect -> read SIDRA: {len(df)} registros")
    return True


def test_get_status() -> bool:
    """Testa get_status() retorna DataFrame valido."""
    import adb

    status = adb.sgs.get_status()
    assert isinstance(status, pd.DataFrame), f"get_status retornou {type(status)}"
    assert not status.empty, "get_status vazio"
    assert "arquivo" in status.columns, f"Colunas: {status.columns.tolist()}"
    assert "status" in status.columns, f"Colunas: {status.columns.tolist()}"

    print(f"  [OK] get_status: {len(status)} indicadores")
    print(status[["arquivo", "status", "registros"]].to_string(index=False))
    return True


def test_available_and_info() -> bool:
    """Testa available() e info()."""
    import adb

    for source_name in adb.available_sources():
        source = getattr(adb, source_name)
        indicators = source.available()
        assert isinstance(indicators, list), (
            f"{source_name}.available() nao retornou list"
        )
        assert len(indicators) > 0, f"{source_name} sem indicadores"

        # info de um indicador
        first = indicators[0]
        info = source.info(first)
        assert isinstance(info, dict), f"{source_name}.info() nao retornou dict"

    print(
        f"  [OK] available() e info() funcionam em todas as {len(adb.available_sources())} fontes"
    )
    return True


def test_multiple_read() -> bool:
    """Testa read com multiplos indicadores."""
    import adb

    df = adb.sgs.read("selic", "cdi", start="2025-01")
    if df.empty:
        print("  [SKIP] Sem dados locais de selic+cdi")
        return True

    assert "selic" in df.columns, f"Colunas: {df.columns.tolist()}"
    assert "cdi" in df.columns, f"Colunas: {df.columns.tolist()}"
    print(f"  [OK] read multiplo (selic + cdi): {len(df)} registros")
    return True


def test_expectations_special_params() -> bool:
    """Testa que read() do Expectations com year/smooth ainda funciona."""
    import adb

    # Dados brutos
    df_raw = adb.expectations.read("selic_anual", start="2025-01")
    if df_raw.empty:
        print("  [SKIP] Sem dados locais de expectations")
        return True

    # Com year (processado)
    df_year = adb.expectations.read("selic_anual", start="2025-01", year=2026)
    assert not df_year.empty, "read com year=2026 vazio"
    assert "selic_anual" in df_year.columns, f"Colunas: {df_year.columns.tolist()}"

    print(
        f"  [OK] Expectations read: bruto={len(df_raw)}, year=2026={len(df_year)} registros"
    )
    return True


if __name__ == "__main__":
    tests = [
        ("available() e info()", test_available_and_info),
        ("collect + read SGS", test_collect_and_read),
        ("collect + read SIDRA", test_collect_sidra),
        ("get_status()", test_get_status),
        ("read multiplo", test_multiple_read),
        ("Expectations params especiais", test_expectations_special_params),
        ("Formato read vs fetch", test_format_compatibility),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"Resultado: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
