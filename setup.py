import os
import sys
import shutil
import sqlite3
import ctypes
from pathlib import Path
import winshell
from win32com.client import Dispatch
from PyInstaller.__main__ import run as pyi_run

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

# Check for admin rights first
if not is_admin():
    print("Requesting administrator privileges...")
    run_as_admin()
    sys.exit()

def get_app_paths():
    # Chemins pour l'installation
    username = os.getenv('USERNAME')
    app_data = os.path.join(os.getenv('LOCALAPPDATA'), 'NMGFacturation')
    data_dir = os.path.join(app_data, 'data')
    install_dir = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'NMGFacturation')
    desktop = str(Path.home() / "Desktop")
    
    return {
        'app_data': app_data,
        'data_dir': data_dir,
        'install_dir': install_dir,
        'desktop': desktop
    }

def create_database(data_dir):
    """Initialise la base de données"""
    db_path = os.path.join(data_dir, 'facturation.db')
    
    # Création des tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dossiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_dossier TEXT,
        adresse_chantier TEXT,
        libelle_travaux TEXT,
        adresse_facturation TEXT,
        acompte_demande REAL,
        moyen_paiement TEXT,
        garantie_decennale TEXT,
        description TEXT,
        devis_signe INTEGER DEFAULT 0,
        facture_payee INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dossier_id INTEGER,
        designation TEXT,
        quantite REAL,
        prix REAL,
        remise REAL,
        unite TEXT,
        FOREIGN KEY (dossier_id) REFERENCES dossiers (id)
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dossier_id INTEGER,
        designation TEXT,
        quantite REAL,
        prix REAL,
        remise REAL,
        unite TEXT,
        FOREIGN KEY (dossier_id) REFERENCES dossiers (id)
    )''')
    
    conn.commit()
    conn.close()
    
    print(f"Base de données créée avec succès dans {db_path}")

def create_shortcut(install_dir, desktop):
    """Crée un raccourci sur le bureau"""
    shortcut_path = os.path.join(desktop, "NMGFacturation.lnk")
    exe_path = os.path.join(install_dir, "NMGFacturation.exe")
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = exe_path
    shortcut.IconLocation = exe_path
    shortcut.save()
    
    print(f"Raccourci créé sur le bureau: {shortcut_path}")

def build_and_install():
    """Construction et installation de l'application"""
    paths = get_app_paths()
    
    # Création des répertoires nécessaires
    os.makedirs(paths['data_dir'], exist_ok=True)
    os.makedirs(paths['install_dir'], exist_ok=True)
    
    # Construction de l'application avec PyInstaller
    pyi_run([
        'src/main.py',
        '--name=NMGFacturation',
        '--windowed',
        f'--icon=src/assets/Img/NMG_CO.ico',
        f'--add-data=src/assets/style.qss;assets/',
        f'--add-data=src/assets/Img/*;assets/Img/',
        '--hidden-import=PyQt5',
        '--hidden-import=sqlite3',
        '--hidden-import=docx',
        '--hidden-import=datetime',
        '--clean',
        '--noconfirm'
    ])
    
    # Copie des fichiers de l'application vers le répertoire d'installation
    dist_path = os.path.join('dist', 'NMGFacturation')
    if os.path.exists(dist_path):
        # Supprimer l'ancienne installation si elle existe
        shutil.rmtree(paths['install_dir'], ignore_errors=True)
        # Copier la nouvelle version
        shutil.copytree(dist_path, paths['install_dir'])
        print(f"Application installée dans {paths['install_dir']}")
    
    # Initialisation de la base de données
    create_database(paths['data_dir'])
    
    # Création du raccourci sur le bureau
    create_shortcut(paths['install_dir'], paths['desktop'])

if __name__ == '__main__':
    try:
        print("Début de l'installation...")
        build_and_install()
        print("Installation terminée avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'installation: {e}")
        sys.exit(1)