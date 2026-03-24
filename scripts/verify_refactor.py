"""
Verificacao do refactor: align-philosophy branch.

Testa:
1. Import limpo (sem CAGED, sem QueryEngine no top-level)
2. available_sources() retorna 5 fontes
3. fetch() existe em todos os explorers
4. fetch() funciona end-to-end (SGS selic - requer internet)
5. read() continua funcionando (se houver dados locais)
"""

import sys


def test_import() -> bool:
    """Testa que o import basico funciona."""
    import adb

    # Sem CAGED
    sources = adb.available_sources()
    assert "caged" not in sources, f"'caged' ainda em sources: {sources}"
    assert len(sources) == 5, f"Esperado 5 fontes, got {len(sources)}: {sources}"

    # Sem QueryEngine/DataManager no top-level
    assert "QueryEngine" not in dir(adb), "QueryEngine ainda exposto no top-level"
    assert "DataManager" not in dir(adb), "DataManager ainda exposto no top-level"

    # Mas acessivel via import direto
    from adb.infra.persistence import QueryEngine, DataManager

    assert QueryEngine is not None
    assert DataManager is not None

    print("[OK] Import limpo")
    return True


def test_fetch_exists() -> bool:
    """Testa que fetch() existe em todos os explorers."""
    import adb

    for source in adb.available_sources():
        explorer = getattr(adb, source)
        assert hasattr(explorer, "fetch"), f"{source} nao tem fetch()"
        assert callable(explorer.fetch), f"{source}.fetch nao eh callable"

    print("[OK] fetch() existe em todos os explorers")
    return True


def test_fetch_sgs() -> bool:
    """Testa fetch stateless do SGS (requer internet)."""
    import adb

    df = adb.sgs.fetch("selic", start="2025-01")
    assert not df.empty, "fetch('selic') retornou vazio"
    assert "selic" in df.columns, (
        f"Coluna 'selic' nao encontrada: {df.columns.tolist()}"
    )
    assert df.index.name == "date", f"Index name: {df.index.name}"
    print(f"[OK] fetch SGS selic: {len(df)} registros desde 2025-01")
    print(df.head(3))
    return True


def test_fetch_ipea() -> bool:
    """Testa fetch stateless do IPEA (requer internet)."""
    import adb

    df = adb.ipea.fetch("caged_saldo", start="2024")
    assert not df.empty, "fetch('caged_saldo') retornou vazio"
    print(f"[OK] fetch IPEA caged_saldo: {len(df)} registros desde 2024")
    print(df.head(3))
    return True


def test_fetch_sidra() -> bool:
    """Testa fetch stateless do SIDRA (requer internet)."""
    import adb

    df = adb.sidra.fetch("ipca", start="2024")
    assert not df.empty, "fetch('ipca') retornou vazio"
    print(f"[OK] fetch SIDRA ipca: {len(df)} registros desde 2024")
    print(df.head(3))
    return True


def test_fetch_expectations() -> bool:
    """Testa fetch stateless de Expectations (requer internet)."""
    import adb

    # Dados brutos
    df = adb.expectations.fetch("selic_anual", start="2025-01")
    assert not df.empty, "fetch('selic_anual') retornou vazio"
    print(f"[OK] fetch Expectations selic_anual: {len(df)} registros")

    # Com processamento (year)
    df2 = adb.expectations.fetch("selic_anual", start="2025-01", year=2026)
    assert not df2.empty, "fetch('selic_anual', year=2026) retornou vazio"
    print(f"[OK] fetch Expectations selic_anual year=2026: {len(df2)} registros")
    return True


def test_fetch_multiple() -> bool:
    """Testa fetch com multiplos indicadores."""
    import adb

    df = adb.sgs.fetch("selic", "cdi", start="2025-01")
    assert not df.empty, "fetch multiplo retornou vazio"
    assert "selic" in df.columns, f"'selic' nao em colunas: {df.columns.tolist()}"
    assert "cdi" in df.columns, f"'cdi' nao em colunas: {df.columns.tolist()}"
    print(f"[OK] fetch multiplo (selic + cdi): {len(df)} registros")
    print(df.head(3))
    return True


def test_read_still_works() -> bool:
    """Testa que read() do cache ainda funciona (se houver dados)."""
    import adb

    df = adb.sgs.read("selic", start="2025-01")
    if df.empty:
        print("[SKIP] read() - sem dados locais (normal se nunca coletou)")
    else:
        print(f"[OK] read SGS selic: {len(df)} registros do cache")
    return True


def test_validation_error() -> bool:
    """Testa que indicador invalido gera erro."""
    import adb

    try:
        adb.sgs.fetch("indicador_inexistente")
        assert False, "Deveria ter dado KeyError"
    except KeyError:
        print("[OK] KeyError para indicador invalido")
    return True


if __name__ == "__main__":
    tests = [
        ("Import limpo", test_import),
        ("fetch() existe", test_fetch_exists),
        ("Validacao de erro", test_validation_error),
        ("read() cache", test_read_still_works),
        ("fetch SGS", test_fetch_sgs),
        ("fetch IPEA", test_fetch_ipea),
        ("fetch SIDRA", test_fetch_sidra),
        ("fetch Expectations", test_fetch_expectations),
        ("fetch multiplo", test_fetch_multiple),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n--- {name} ---")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"Resultado: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
