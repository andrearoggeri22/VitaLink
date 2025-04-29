import polib
from pathlib import Path

def compile_po_to_mo(po_path: Path) -> bool:
    try:
        mo_path = po_path.with_suffix(".mo")
        polib.pofile(po_path).save_as_mofile(mo_path)
        print(f"✅  {po_path.relative_to(BASE_DIR)} → {mo_path.name}")
        return True
    except Exception as exc:
        print(f"NO {po_path}: {exc}")
        return False

BASE_DIR = Path(__file__).resolve().parent / "translations"

def main() -> None:
    po_files = BASE_DIR.glob("*/*/LC_MESSAGES/*.po")  # es. it/LC_MESSAGES/messages.po
    results = [compile_po_to_mo(po) for po in po_files]
    print(
        f"\nCompiled {sum(results)} / {len(results)} catalog(s)"
        f" in {BASE_DIR.relative_to(Path.cwd())}"
    )

if __name__ == "__main__":
    main()