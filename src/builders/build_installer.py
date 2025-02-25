import PyInstaller.__main__

def create_installer():
    """Crée l'installateur"""
    PyInstaller.__main__.run([
        'tools/installer_app.py',
        '--name=NMGFacturationInstaller',
        '--onefile',
        '--uac-admin',
        '--icon=src/assets/Img/NMG_CO.ico',
        '--hidden-import=winshell',
        '--hidden-import=win32com.client', 
        '--hidden-import=win32api',
        '--hidden-import=PyQt5',
        '--hidden-import=requests',
        '--add-data=src/assets/Img/NMG_CO.ico;assets/Img',
        '--windowed',
        '--clean',
        '--noconfirm'
    ])

if __name__ == '__main__':
    create_installer()