from pathlib import Path
import sys
import pandas as pd

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from mte.caged.collector import CAGEDCollector


def main():
    print("Iniciando verificacao de consolidacao anual...")

    data_path = project_root / "data"
    collector = CAGEDCollector(data_path)

    # Consolidar (vai ler do raw e salvar no processed separado por ano)
    # Usamos verbose=True para ver o progresso
    results = collector.consolidate(verbose=True)

    print("\nVerificacao dos arquivos gerados em processed/mte/caged:")
    processed_dir = data_path / "processed" / "mte" / "caged"

    if processed_dir.exists():
        for f in processed_dir.glob("*.parquet"):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  {f.name}: {size_mb:.2f} MB")
    else:
        print("  Diretorio processed nao encontrado!")


if __name__ == "__main__":
    main()
