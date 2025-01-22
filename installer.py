import PyInstaller.__main__
import os

def create_app():
    # Première étape: Création de l'application principale
    PyInstaller.__main__.run([
        'src/main.py',
        '--name=NMGFacturation',
        '--onefile',
        '--icon=src/assets/Img/NMG_CO.ico',
        '--add-data=src/assets;assets',
        '--hidden-import=PyQt5',
        '--hidden-import=sqlite3',
        '--hidden-import=src.utils.generate_devis',  # Ajouter ces imports
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

def create_installer():
    # Deuxième étape: Création de l'installateur
    PyInstaller.__main__.run([
        'setup.py',
        '--name=NMGFacturationInstaller',
        '--onefile',
        '--uac-admin',
        '--icon=src/assets/Img/NMG_CO.ico',
        '--add-data=dist/NMGFacturation.exe;.',  # Inclure l'application compilée
        '--hidden-import=winshell',
        '--hidden-import=win32com.client', 
        '--hidden-import=win32api',
        '--windowed',
        '--clean',
        '--noconfirm'
    ])

if __name__ == '__main__':
    create_app()
    create_installer()