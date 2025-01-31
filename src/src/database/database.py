import os
import sqlite3
import sys
from .databaseinit import init_database

def get_db_path():
    """Retourne le chemin de la base de données dans AppData"""
    appdata = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation')
    data_dir = os.path.join(appdata, 'data')
    os.makedirs(appdata, exist_ok=True)
    return os.path.join(data_dir, 'facturation.db')

# Utiliser le chemin dans AppData
DB_PATH = get_db_path()

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    """Initialise la base de données"""
    init_database()

def add_dossier(numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO dossiers (
        numero_dossier, 
        adresse_chantier, 
        libelle_travaux, 
        adresse_facturation, 
        moyen_paiement, 
        garantie_decennale, 
        description, 
        devis_signe, 
        facture_payee
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee))
    dossier_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return dossier_id

def update_dossier(dossier_id, numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee):
    """Met à jour un dossier existant dans la base de données."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE dossiers 
            SET numero_dossier = ?, 
                adresse_chantier = ?, 
                libelle_travaux = ?, 
                adresse_facturation = ?,
                moyen_paiement = ?, 
                garantie_decennale = ?, 
                description = ?, 
                devis_signe = ?,  
                facture_payee = ?  
            WHERE id = ?
        ''', (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee, dossier_id))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour du dossier : {e}")
        return False

def delete_produits(dossier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM produits
    WHERE dossier_id = ?
    ''', (dossier_id,))
    conn.commit()
    conn.close()

def add_produit(dossier_id, designation, quantite, prix, remise, unite):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute('''
        INSERT INTO produits (dossier_id, designation, quantite, prix, remise, unite)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (dossier_id, designation, quantite, prix, remise, unite))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def add_option(dossier_id, designation, quantite, prix, remise, unite):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute('''
        INSERT INTO options (dossier_id, designation, quantite, prix, remise, unite)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (dossier_id, designation, quantite, prix, remise, unite))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_options(dossier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM options
    WHERE dossier_id = ?
    ''', (dossier_id,))
    conn.commit()
    conn.close()

def delete_dossier(dossier_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute('DELETE FROM options WHERE dossier_id = ?', (dossier_id,))
        cursor.execute('DELETE FROM produits WHERE dossier_id = ?', (dossier_id,))
        cursor.execute('DELETE FROM dossiers WHERE id = ?', (dossier_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_dossiers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dossiers')
    dossiers = cursor.fetchall()
    conn.close()
    return dossiers

def get_dossier(dossier_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM dossiers WHERE id = ?
        ''', (dossier_id,))
        dossier = cursor.fetchone()
        conn.close()
        if dossier is None:
            raise ValueError(f"Le dossier {dossier_id} n'existe pas")
        return dossier  # Retourne un tuple ou None
    except Exception as e:
        print(f"Erreur lors de la récupération du dossier : {e}")
        return None  # Au lieu d'un entier, retourner None en cas d'erreur

def get_produits(dossier_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produits WHERE dossier_id = ?', (dossier_id,))
        produits = cursor.fetchall()
        conn.close()
        return produits if produits else []
    except Exception as e:
        print(f"Erreur lors de la récupération des produits : {e}")
        return []

def get_options(dossier_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM options WHERE dossier_id = ?', (dossier_id,))
        options = cursor.fetchall()
        conn.close()
        return options if options else []
    except Exception as e:
        print(f"Erreur lors de la récupération des options : {e}")
        return []

def get_addresses():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, address FROM addresses')
        addresses = cursor.fetchall()
        conn.close()
        return addresses
    except Exception as e:
        print(f"Erreur lors de la récupération des adresses : {e}")
        return []

if __name__ == "__main__":
    create_tables()