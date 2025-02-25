import PyInstaller.__main__
from src.version import APP_VERSION

def build_app():
    """Compile l'application principale en exécutable"""
    PyInstaller.__main__.run([
        'src/main.py',
        f'--name=NMGFacturation_v{APP_VERSION}',
        '--onefile',
        '--icon=src/assets/Img/NMG_CO.ico',
        '--add-data=src/assets;assets',
        '--hidden-import=PyQt5',
        '--hidden-import=sqlite3',
        '--hidden-import=src.utils.generate_devis',
        '--hidden-import=src.utils.generate_facture',
        '--hidden-import=src.database',
        '--hidden-import=src.database.database',
        '--hidden-import=src.database.databaseinit',
        '--hidden-import=docx',
        '--collect-submodules=src',
        '--collect-data=src',
        '--windowed',
        '--clean',
        '--noconfirm'
    ])

if __name__ == '__main__':
    build_app()