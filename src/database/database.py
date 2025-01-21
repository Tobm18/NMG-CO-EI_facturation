import os
import sqlite3
import sys
from .databaseinit import init_database

def get_db_path():
    """Retourne le chemin de la base de données dans AppData"""
    appdata = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation')
    os.makedirs(appdata, exist_ok=True)
    return os.path.join(appdata, 'facturation.db')

# Utiliser le chemin dans AppData
DB_PATH = get_db_path()

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    """Initialise la base de données"""
    init_database()

def add_dossier(numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO dossiers (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee))
    dossier_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return dossier_id

def update_dossier(dossier_id, numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE dossiers
    SET numero_dossier = ?, adresse_chantier = ?, libelle_travaux = ?, adresse_facturation = ?, acompte_demande = ?, moyen_paiement = ?, garantie_decennale = ?, description = ?, devis_signe = ?, facture_payee = ?
    WHERE id = ?
    ''', (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description, devis_signe, facture_payee, dossier_id))
    conn.commit()
    conn.close()

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

def get_produits(dossier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produits WHERE dossier_id = ?', (dossier_id,))
    produits = cursor.fetchall()
    conn.close()
    return produits

def get_options(dossier_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM options WHERE dossier_id = ?', (dossier_id,))
    options = cursor.fetchall()
    conn.close()
    return options

if __name__ == "__main__":
    create_tables()