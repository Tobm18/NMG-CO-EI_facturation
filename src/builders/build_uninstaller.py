import PyInstaller.__main__
import os

def create_uninstaller():
    PyInstaller.__main__.run([
        'tools/uninstaller_app.py',
        '--name=NMGFacturationUninstaller',
        '--onefile',
        '--uac-admin', 
        '--icon=src/assets/Img/NMG_CO.ico',
        '--hidden-import=winshell',
        '--hidden-import=win32api',
        '--windowed',
        '--clean',
        '--noconfirm'
    ])

if __name__ == '__main__':
    create_uninstaller()