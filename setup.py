import os
import sys
import shutil
import sqlite3
import ctypes
from pathlib import Path
import winshell
from win32com.client import Dispatch

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def get_app_paths():
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

def copy_application_files():
    """Copie les fichiers de l'application depuis les ressources embarquées"""
    paths = get_app_paths()
    
    # Obtenez le chemin du bundle PyInstaller
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    # Copie de l'exécutable principal
    app_exe = os.path.join(bundle_dir, 'NMGFacturation.exe')
    if os.path.exists(app_exe):
        shutil.copy2(app_exe, os.path.join(paths['install_dir'], 'NMGFacturation.exe'))
        print(f"Application copiée vers {paths['install_dir']}")

def main():
    if not is_admin():
        print("Requesting administrator privileges...")
        run_as_admin()
        sys.exit()

    try:
        print("Début de l'installation...")
        paths = get_app_paths()
        
        # Création des répertoires
        os.makedirs(paths['data_dir'], exist_ok=True)
        os.makedirs(paths['install_dir'], exist_ok=True)
        
        # Copie des fichiers de l'application
        copy_application_files()
        
        # Initialisation de la base de données
        create_database(paths['data_dir'])
        
        # Création du raccourci
        create_shortcut(paths['install_dir'], paths['desktop'])
        
        # Remplacer input() par un message box
        from win32api import MessageBox
        MessageBox(None, "Installation terminée avec succès!", "Installation")
        
    except Exception as e:
        from win32api import MessageBox
        MessageBox(None, f"Erreur lors de l'installation: {e}", "Erreur")
        sys.exit(1)

if __name__ == '__main__':
    main()