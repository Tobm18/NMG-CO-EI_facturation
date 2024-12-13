import sqlite3

def create_tables():
    conn = sqlite3.connect('facturation.db')
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
        description TEXT
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

    conn.commit()
    conn.close()

def add_dossier(numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description):
    conn = sqlite3.connect('facturation.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO dossiers (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description))
    dossier_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return dossier_id

def update_dossier(dossier_id, numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description):
    conn = sqlite3.connect('facturation.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE dossiers
    SET numero_dossier = ?, adresse_chantier = ?, libelle_travaux = ?, adresse_facturation = ?, acompte_demande = ?, moyen_paiement = ?, garantie_decennale = ?, description = ?
    WHERE id = ?
    ''', (numero_dossier, adresse_chantier, libelle_travaux, adresse_facturation, acompte_demande, moyen_paiement, garantie_decennale, description, dossier_id))
    conn.commit()
    conn.close()

def delete_produits(dossier_id):
    conn = sqlite3.connect('facturation.db')
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM produits
    WHERE dossier_id = ?
    ''', (dossier_id,))
    conn.commit()
    conn.close()

def add_produit(dossier_id, designation, quantite, prix, remise, unite):
    conn = sqlite3.connect('facturation.db')
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

def get_dossiers():
    conn = sqlite3.connect('facturation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dossiers')
    dossiers = cursor.fetchall()
    conn.close()
    return dossiers

def get_produits(dossier_id):
    conn = sqlite3.connect('facturation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produits WHERE dossier_id = ?', (dossier_id,))
    produits = cursor.fetchall()
    conn.close()
    return produits

if __name__ == "__main__":
    create_tables()