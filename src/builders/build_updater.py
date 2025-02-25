import PyInstaller.__main__

def build_updater():
    """Compile l'updater en exécutable"""
    PyInstaller.__main__.run([
        'tools/updater_app.py',
        '--name=NMGFacturationUpdater',
        '--onefile',
        '--icon=src/assets/Img/NMG_CO.ico',
        '--hidden-import=PyQt5',
        '--hidden-import=requests',
        '--windowed',
        '--clean',
        '--noconfirm'
    ])

if __name__ == '__main__':
    build_updater()