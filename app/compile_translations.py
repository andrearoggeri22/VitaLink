"""
Translation Compilation Module.

This module provides functionality for compiling translation files (.po files) into
binary message catalog files (.mo files) that can be used by the application's
internationalization system.

The module:
1. Finds all .po files in the translations directory
2. Compiles each .po file into a corresponding .mo file
3. Reports on the success or failure of each compilation
4. Provides summary statistics of the compilation process

This script can be run directly to compile all translation files at once.
"""

import polib
from pathlib import Path

def compile_po_to_mo(po_path: Path) -> bool:
    """
    Compile a PO translation file to a binary MO file.
    
    This function takes a path to a PO (Portable Object) translation file and
    compiles it to an MO (Machine Object) binary file that can be efficiently
    used by gettext at runtime.
    
    Args:
        po_path (Path): Path object pointing to the .po file to compile
        
    Returns:
        bool: True if compilation was successful, False otherwise
        
    Side effects:
        - Creates or overwrites an .mo file with the same base name as the input file
        - Prints status messages to standard output
    """
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
    """
    Main function to compile all translation files.
    
    This function:
    1. Finds all .po files in the translations directory structure
    2. Compiles each one to a corresponding .mo file
    3. Reports the number of successful and failed compilations
    
    The function searches for translation files in the standard directory structure:
    translations/[language]/LC_MESSAGES/[domain].po
    
    Returns:
        None
    """
    po_files = BASE_DIR.glob("*/*/LC_MESSAGES/*.po")  # es. it/LC_MESSAGES/messages.po
    results = [compile_po_to_mo(po) for po in po_files]
    print(
        f"\nCompiled {sum(results)} / {len(results)} catalog(s)"
        f" in {BASE_DIR.relative_to(Path.cwd())}"
    )

if __name__ == "__main__":
    main()