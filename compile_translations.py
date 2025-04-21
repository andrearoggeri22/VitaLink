import os
import polib

def compile_po_to_mo(po_file_path):
    try:
        # Load the .po file
        po = polib.pofile(po_file_path)
        
        # Get the path for the .mo file
        mo_file_path = po_file_path.replace('.po', '.mo')
        
        # Save as .mo
        po.save_as_mofile(mo_file_path)
        print(f"Successfully compiled {po_file_path} to {mo_file_path}")
        return True
    except Exception as e:
        print(f"Error compiling {po_file_path}: {str(e)}")
        return False

if __name__ == "__main__":
    # Path to the messages.po file
    po_file_path = 'translations/it/LC_MESSAGES/messages.po'
    
    # Compile the translations
    success = compile_po_to_mo(po_file_path)
    
    if success:
        print("Translation compilation completed successfully")
    else:
        print("Translation compilation failed")