import os
import sqlite3
import stat
import sys
import ctypes
from ctypes import wintypes
import getpass
import subprocess

def get_real_windows_user():
    """Récupère l'utilisateur qui a réellement exécuté le script"""
    try:
        # Essayer d'abord avec la variable d'environnement SUDO_USER (pour les commandes sudo)
        sudo_user = os.environ.get('SUDO_USER')
        if sudo_user:
            return sudo_user

        # Ensuite essayer avec USERNAME ou USER
        username = os.environ.get('USERNAME') or os.environ.get('USER')
        if username:
            return username

        # Sinon utiliser getpass
        return getpass.getuser()
    except:
        return None

def get_real_appdata_path():
    """Récupère le vrai chemin AppData Local en contournant la sandbox Windows Store"""
    try:
        # Utiliser une commande système pour obtenir le vrai chemin
        cmd = 'echo %USERPROFILE%'
        user_profile = subprocess.check_output(cmd, shell=True).decode().strip()
        real_path = os.path.join(user_profile, 'AppData', 'Local', 'NMGFacturation')
        print(f"Chemin réel AppData détecté: {real_path}")
        return real_path
    except Exception as e:
        print(f"Erreur lors de la détection du chemin réel: {e}")
        # Fallback au chemin standard
        return os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'NMGFacturation')

def init_database():
    try:
        # Créer le dossier dans AppData
        appdata_dir = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation')
        data_dir = os.path.join(appdata_dir, 'data')
        os.makedirs(appdata_dir, exist_ok=True)
        
        print(f"Création de la base de données dans : {data_dir}")
        
        # Chemin de la base de données
        db_path = os.path.join(data_dir, 'facturation.db')
        print(f"Tentative de création de la base de données à : {db_path}")

        # Test write permissions
        try:
            with open(db_path, 'a') as f:
                pass
        except Exception as e:
            print(f"Erreur de permissions lors de l'accès au fichier : {e}")
            raise e

        # Create database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
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
            facture_payee INTEGER DEFAULT 0,
            devis_generated INTEGER DEFAULT 0,  
            facture_generated INTEGER DEFAULT 0
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
        
        # Verify file exists and is accessible
        if os.path.isfile(db_path):
            file_size = os.path.getsize(db_path)
            print(f"Base de données créée avec succès. Taille du fichier: {file_size} bytes")
        else:
            print("ERREUR: Le fichier n'a pas été créé correctement")
            return False
            
        return True
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
        raise e

if __name__ == '__main__':
    init_database()