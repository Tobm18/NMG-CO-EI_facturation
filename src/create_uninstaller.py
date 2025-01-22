import PyInstaller.__main__
import os

def create_uninstaller():
    PyInstaller.__main__.run([
        'uninstaller.py',
        '--name=NMGFacturationUninstaller',
        '--onefile',
        '--uac-admin',  # Demande les privilèges admin
        '--icon=src/assets/Img/NMG_CO.ico',
        '--hidden-import=winshell',
        '--hidden-import=win32api',
        '--windowed',
        '--clean',
        '--noconfirm'
    ])

if __name__ == '__main__':
    create_uninstaller()