import os
import sys
import shutil
import winshell
import requests
import ctypes
import sqlite3
from win32com.client import Dispatch
from PyQt5.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt

DOWNLOAD_URL = "https://nmg.skietmontagnepegomas.com"
APP_VERSION = "1.1.0"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def get_app_paths():
    """Retourne les chemins importants de l'application"""
    return {
        'install_dir': os.path.join(os.environ['PROGRAMFILES'], 'NMGFacturation'),
        'desktop': winshell.desktop(),
        'app_data': os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation')
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
        moyen_paiement TEXT,
        garantie_decennale INTEGER,
        description TEXT,
        devis_signe INTEGER DEFAULT 0,
        facture_payee INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dossier_id INTEGER,
        designation TEXT,
        quantite TEXT,
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
        quantite TEXT,
        prix REAL,
        remise REAL,
        unite TEXT,
        FOREIGN KEY (dossier_id) REFERENCES dossiers (id)
    )''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE
        )
        ''')

    conn.commit()
    conn.close()
    
    print(f"Base de données créée avec succès dans {db_path}")

def create_shortcut(target_path, shortcut_path):
    """Crée un raccourci Windows"""
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.IconLocation = target_path
    shortcut.save()

def get_latest_version():
    """Récupère la dernière version disponible"""
    try:
        response = requests.get(f"{DOWNLOAD_URL}/update/check")
        if response.status_code == 200:
            update_info = response.json()
            return update_info.get('version')
    except Exception as e:
        print(f"Erreur lors de la vérification de version: {e}")
        return None

def download_file(url, progress_dialog):
    """Télécharge un fichier avec barre de progression"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(os.environ['TEMP'], os.path.basename(url))
            
            with open(file_path, 'wb') as f:
                total_length = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if progress_dialog.wasCanceled():
                        return None
                    if chunk:
                        downloaded += len(chunk)
                        f.write(chunk)
                        if total_length:
                            progress_dialog.setValue(int(100 * downloaded / total_length))
                            
            return file_path
    except Exception as e:
        print(f"Erreur lors du téléchargement: {e}")
        return None

def install_application():
    """Installe l'application"""
    try:
        # Récupérer la dernière version
        version = get_latest_version()
        if not version:
            QMessageBox.critical(None, "Erreur", "Impossible de récupérer la version de l'application")
            return False

        # Créer les dossiers nécessaires
        paths = get_app_paths()
        os.makedirs(paths['install_dir'], exist_ok=True)

        # Créer le dossier data et initialiser la base de données
        data_dir = os.path.join(paths['app_data'], 'data')
        os.makedirs(data_dir, exist_ok=True)
        create_database(data_dir)

        # Dialogue de progression
        progress = QProgressDialog("Téléchargement en cours...", "Annuler", 0, 100)
        progress.setWindowModality(Qt.WindowModal)
        
        # Télécharger l'updater
        progress.setLabelText("Téléchargement de l'updater...")
        updater = download_file(f"{DOWNLOAD_URL}/download/updater", progress)
        if not updater:
            raise Exception("Échec du téléchargement de l'updater")

        # Télécharger l'application principale
        progress.setLabelText("Téléchargement de l'application...")
        progress.setValue(0)
        app = download_file(f"{DOWNLOAD_URL}/download/{version}", progress)
        if not app:
            raise Exception("Échec du téléchargement de l'application")

        progress.setLabelText("Installation...")
        
        # Copier les fichiers
        shutil.copy2(updater, os.path.join(paths['install_dir'], 'NMGFacturationUpdater.exe'))
        shutil.copy2(app, os.path.join(paths['install_dir'], 'NMGFacturation.exe'))
        
        # Créer le raccourci
        create_shortcut(
            os.path.join(paths['install_dir'], 'NMGFacturation.exe'),
            os.path.join(paths['desktop'], 'NMGFacturation.lnk')
        )
        
        # Nettoyer
        os.remove(updater)
        os.remove(app)
        progress.close()
        
        QMessageBox.information(None, "Installation", "Installation terminée avec succès!")
        return True
        
    except Exception as e:
        QMessageBox.critical(None, "Erreur", f"Erreur lors de l'installation: {e}")
        return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    install_application()