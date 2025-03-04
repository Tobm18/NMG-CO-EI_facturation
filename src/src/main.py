import os
import datetime
import sys
import requests
import sqlite3
from pathlib import Path
from src.version import APP_VERSION
import subprocess
from PyQt5.QtNetwork import QLocalSocket, QLocalServer

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if (project_root not in sys.path):
    sys.path.append(project_root)

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QFormLayout, QLineEdit, QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QLabel, QStackedLayout, QHeaderView, QSplitter,
    QComboBox, QCheckBox, QScrollArea, QTextEdit, QMenu, QDialog,
    QDialogButtonBox, QSizePolicy, QAbstractItemView, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

from src.database.database import (
    get_dossiers,
    get_produits, 
    get_options,
    update_dossier,
    add_dossier,
    add_produit,
    add_option,
    delete_dossier,
    delete_produits as delete_produits,
    delete_options as delete_options,
    create_tables,
    get_addresses,
    update_document_generated
)
from src.database.databaseinit import init_database
from src.views.liste_facture import ListeFacture
from src.views.liste_devis import ListeDevis
from src.views.manage_addresses import ManageAddressesDialog

def load_stylesheet():
    try:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
            style_path = os.path.join(base_path, 'assets', 'style.qss')
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            style_path = os.path.join(base_path, 'src', 'assets', 'style.qss')

        if not os.path.exists(style_path):
            print(f"Style file not found at: {style_path}")
            return ""
            
        with open(style_path, 'r') as f:
            style = f.read()
            
        # Remplacer les chemins d'images dans le QSS
        if getattr(sys, 'frozen', False):
            img_path = os.path.join(base_path, 'assets', 'Img').replace('\\', '/')
        else:
            img_path = os.path.join(base_path, 'src', 'assets', 'Img').replace('\\', '/')
            
        # Remplacer les références relatives par des chemins absolus
        style = style.replace('url(', f'url({img_path}/')
        return style
        
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
        return ""

def get_resource_path(relative_path):
    """Obtient le chemin absolu d'une ressource, que ce soit en développement ou dans l'exe"""
    try:
        if getattr(sys, 'frozen', False):
            # Si l'application est compilée (dans un exe)
            base_path = sys._MEIPASS
            return os.path.join(base_path, 'assets', relative_path)
        else:
            # Si l'application est en développement
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, 'src', 'assets', relative_path)
    except Exception as e:
        print(f"Erreur lors de la récupération du chemin de la ressource : {e}")
        return None

def is_app_running():
    """Vérifie si une autre instance de l'application est déjà en cours d'exécution"""
    socket = QLocalSocket()
    socket.connectToServer("NMGFacturation")
    is_running = socket.waitForConnected(500)
    if is_running:
        socket.write(b"ACTIVATE")
        socket.flush()
        socket.disconnectFromServer()
    return is_running

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class NoScrollQuantityComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._enabled = False
        
    def wheelEvent(self, event):
        event.ignore()
        
    def setEditMode(self, editable):
        self._enabled = editable
        self.setEnabled(editable)
        self.lineEdit().setReadOnly(not editable)

    def showPopup(self):
        if self._enabled:
            super().showPopup()

    def mousePressEvent(self, event):
        if self._enabled:
            super().mousePressEvent(event)
        else:
            event.ignore()

class DatabaseWarningDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Base de données manquante")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        message = QLabel(
            "La base de données est manquante ou corrompue.\n"
            "Voulez-vous créer une nouvelle base de données ?"
        )
        message.setWordWrap(True)
        layout.addWidget(message)
        
        self.create_btn = QPushButton("Créer une nouvelle base de données")
        self.create_btn.clicked.connect(self.accept)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        self.cancel_btn = QPushButton("Quitter")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        layout.addWidget(self.create_btn)
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)

def verify_database():
    """Vérifie si la base de données existe et est valide"""
    try:
        db_path = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation', 'data', 'facturation.db')
        
        # Vérifier si le fichier existe
        if not os.path.exists(db_path):
            return False
            
        # Tenter d'ouvrir la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Définir le schéma attendu pour chaque table
        expected_schema = {
            'dossiers': [
                'id', 'numero_dossier', 'adresse_chantier', 'libelle_travaux',
                'adresse_facturation', 'moyen_paiement', 'garantie_decennale',
                'description', 'devis_signe', 'facture_payee',
                'devis_generated', 'facture_generated'
            ],
            'produits': [
                'id', 'dossier_id', 'designation', 'quantite',
                'prix', 'remise', 'unite'
            ],
            'options': [
                'id', 'dossier_id', 'designation', 'quantite',
                'prix', 'remise', 'unite'
            ],
            'addresses': [
                'id', 'address'
            ]
        }
        
        # Vérifier chaque table
        for table_name, expected_columns in expected_schema.items():
            # Vérifier si la table existe
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """)
            if not cursor.fetchone():
                print(f"Table manquante: {table_name}")
                return False
                
            # Vérifier les colonnes
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            # Vérifier si toutes les colonnes attendues sont présentes
            missing_columns = set(expected_columns) - set(existing_columns)
            if missing_columns:
                print(f"Colonnes manquantes dans {table_name}: {missing_columns}")
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erreur lors de la vérification de la base de données : {e}")
        return False

def initialize_database():
    """Initialise ou vérifie la base de données"""
    db_path = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation', 'data', 'facturation.db')
    db_dir = os.path.dirname(db_path)
    
    if not os.path.exists(db_path) or not verify_database():
        dialog = DatabaseWarningDialog()
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Si le dossier data existe, supprimer son contenu
                if os.path.exists(db_dir):
                    try:
                        # On force la fermeture de toutes les connexions existantes
                        import gc
                        gc.collect()  # Force garbage collection
                        
                        # Si une connexion existe, on la ferme
                        try:
                            conn = sqlite3.connect(db_path)
                            conn.close()
                        except:
                            pass
                        
                        # Petite pause pour s'assurer que les connexions sont bien fermées
                        import time
                        time.sleep(0.5)
                        
                        # Supprimer tous les fichiers dans le dossier data
                        for filename in os.listdir(db_dir):
                            file_path = os.path.join(db_dir, filename)
                            if os.path.isfile(file_path):
                                try:
                                    os.remove(file_path)
                                except PermissionError:
                                    # Si on ne peut toujours pas supprimer, on attend encore
                                    time.sleep(0.5)
                                    os.remove(file_path)
                    except Exception as e:
                        QMessageBox.critical(None, "Erreur", f"Erreur lors de la suppression des anciens fichiers : {str(e)}")
                        return False

                # Créer le dossier data s'il n'existe pas
                os.makedirs(db_dir, exist_ok=True)
                
                # Initialiser la nouvelle base de données
                from src.database.databaseinit import init_database
                init_database()
                QMessageBox.information(None, "Succès", "Base de données créée avec succès.")
                return True
            except Exception as e:
                QMessageBox.critical(None, "Erreur", f"Erreur lors de la création de la base de données : {str(e)}")
                return False
        else:
            return False
    return True

class BackupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sauvegarde/Restauration")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        # Bouton de sauvegarde
        self.backup_btn = QPushButton("Sauvegarder l'application")
        self.backup_btn.clicked.connect(self.backup)
        self.backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 4px;
                margin: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        # Bouton de restauration
        self.restore_btn = QPushButton("Restaurer une sauvegarde")
        self.restore_btn.clicked.connect(self.restore)
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 4px;
                margin: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        layout.addWidget(self.backup_btn)
        layout.addWidget(self.restore_btn)
        self.setLayout(layout)

    def backup(self):
        try:
            # Obtenir le chemin de la base de données source
            db_path = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation', 'data', 'facturation.db')
            if not os.path.exists(db_path):
                QMessageBox.warning(self, "Erreur", "Base de données introuvable")
                return

            # Générer le nom du fichier avec la date et l'heure actuelles
            current_time = datetime.datetime.now()
            backup_filename = f"Sauvegarde_{current_time.strftime('%d-%m-%Y_%Hh%M')}.db"

            # Demander à l'utilisateur où sauvegarder le fichier
            default_path = os.path.join(os.path.expanduser("~/Desktop"), backup_filename)
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Sauvegarder la base de données",
                default_path,
                "Database Files (*.db)"
            )
            
            if file_path:
                # Copier le fichier
                import shutil
                shutil.copy2(db_path, file_path)
                QMessageBox.information(self, "Succès", "Sauvegarde effectuée avec succès")
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")

    def restore(self):
        try:
            # Select backup file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Sélectionner une sauvegarde",
                os.path.expanduser("~/Desktop"),
                "Database Files (*.db)"
            )
            
            if file_path:
                reply = QMessageBox.question(
                    self,
                    'Confirmation',
                    'La restauration remplacera la base de données actuelle. Continuer ?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Get paths
                    db_path = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation', 'data', 'facturation.db')
                    db_dir = os.path.dirname(db_path)
                    os.makedirs(db_dir, exist_ok=True)
                    
                    # Create new database with current schema
                    from src.database.databaseinit import init_database
                    init_database()
    
                    # Connect to both databases
                    old_conn = sqlite3.connect(file_path)
                    new_conn = sqlite3.connect(db_path)
                    
                    try:
                        old_cursor = old_conn.cursor()
                        new_cursor = new_conn.cursor()
    
                        # Transfer dossiers data
                        old_cursor.execute("SELECT * FROM dossiers")
                        dossiers = old_cursor.fetchall()
                        
                        for dossier in dossiers:
                            # Add missing columns with default values
                            dossier_data = list(dossier)
                            if len(dossier_data) < 12:  # If old schema
                                dossier_data.extend([0, 0])  # Add devis_generated and facture_generated
                            
                            new_cursor.execute('''
                                INSERT INTO dossiers (
                                    id, numero_dossier, adresse_chantier, libelle_travaux,
                                    adresse_facturation, moyen_paiement, garantie_decennale,
                                    description, devis_signe, facture_payee,
                                    devis_generated, facture_generated
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', dossier_data)
    
                        # Transfer produits data
                        old_cursor.execute("SELECT * FROM produits")
                        produits = old_cursor.fetchall()
                        for produit in produits:
                            new_cursor.execute('''
                                INSERT INTO produits (
                                    id, dossier_id, designation, quantite,
                                    prix, remise, unite
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', produit)
    
                        # Transfer options data
                        old_cursor.execute("SELECT * FROM options")
                        options = old_cursor.fetchall()
                        for option in options:
                            new_cursor.execute('''
                                INSERT INTO options (
                                    id, dossier_id, designation, quantite,
                                    prix, remise, unite
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', option)
    
                        # Transfer addresses data
                        old_cursor.execute("SELECT * FROM addresses")
                        addresses = old_cursor.fetchall()
                        for address in addresses:
                            new_cursor.execute('INSERT INTO addresses (id, address) VALUES (?, ?)', address)
    
                        new_conn.commit()
                        msg = QMessageBox.information(
                            self, 
                            "Succès", 
                            "Base de données restaurée avec succès, veuillez redémarrer l'application",
                            QMessageBox.Ok
                        )
                        if msg == QMessageBox.Ok:
                            sys.exit(0)  # Exit application
                        
                    except Exception as e:
                        QMessageBox.critical(self, "Erreur", f"Erreur lors de la restauration : {str(e)}")
                        
                    finally:
                        old_conn.close()
                        new_conn.close()
    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la restauration : {str(e)}")

class MainWindow(QWidget):
    APP_VERSION = APP_VERSION
    
    def __init__(self):
        super().__init__()
        self.update_url = "https://nmg.skietmontagnepegomas.com/update"
        
        self.setWindowTitle("NMG&CO EI Facturation")
        self.setGeometry(100, 100, 1280, 720)  # Set window size to 1280x720 for 16:9 aspect ratio
        self.setMinimumSize(1280, 720)  # Set minimum size to ensure usability on smaller screens
        
        # Définition correcte de l'icône de la fenêtre principale
        icon_path = get_resource_path(os.path.join('Img', 'NMG_CO.ico'))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icône non trouvée : {icon_path}")

        # Layout principal
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Bandeau en haut de la page
        bandeau_layout = QHBoxLayout()
        bandeau_layout.setSpacing(0)
        bandeau_layout.setContentsMargins(10, 0, 0, 0)  # Marge gauche de 10px
        
        # Bouton de sauvegarde avec l'icône
        self.save_button_bandeau = QPushButton("  Sauvegarde")
        self.save_button_bandeau.setFixedWidth(130)  # Augmenter la largeur pour accommoder le texte
        save_icon_path = get_resource_path(os.path.join('Img', 'save.png'))
        if os.path.exists(save_icon_path):
            icon = QIcon(save_icon_path)
            if not icon.isNull():
                self.save_button_bandeau.setIcon(icon)
                self.save_button_bandeau.setIconSize(QSize(20, 20))
            else:
                print(f"L'icône n'a pas pu être chargée : {save_icon_path}")
        else:
            print(f"Fichier d'icône non trouvé : {save_icon_path}")
            
        self.save_button_bandeau.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                min-width: 130px;
                max-width: 130px;
                min-height: 50px;
                max-height: 50px;
                color: white;
                font-size: 14px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 0px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)

        # Modifier la connexion du bouton de sauvegarde
        self.save_button_bandeau.clicked.connect(self.show_backup_dialog)

        # Ajouter un widget pour créer un espace flexible
        bandeau_layout.addWidget(self.save_button_bandeau)
        bandeau_layout.addStretch(1)  # Ajouter un espace flexible
        
        # Ajouter les autres boutons
        self.dossiers_button = QPushButton("Liste des Dossiers")
        self.dossiers_button.setStyleSheet(self.get_button_style(True))
        self.dossiers_button.clicked.connect(self.show_dossiers)

        self.factures_button = QPushButton("Liste des Factures")
        self.factures_button.setStyleSheet(self.get_button_style(False))
        self.factures_button.clicked.connect(self.show_factures)

        self.devis_button = QPushButton("Liste des Devis")
        self.devis_button.setStyleSheet(self.get_button_style(False))
        self.devis_button.clicked.connect(self.show_devis)

        self.adresses_button = QPushButton("Liste des Adresses")
        self.adresses_button.setStyleSheet(self.get_button_style(False))
        self.adresses_button.clicked.connect(self.show_addresses)

        # Ajouter un label pour la version à droite
        version_label = QLabel(f"v{self.APP_VERSION}")
        version_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 12px;
                padding-right: 10px;
            }
        """)
        version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        bandeau_layout.addWidget(version_label)  # Ajouter le label de version
        bandeau_layout.addWidget(self.dossiers_button)
        bandeau_layout.addWidget(self.factures_button)
        bandeau_layout.addWidget(self.devis_button)
        bandeau_layout.addWidget(self.adresses_button)
        
        bandeau_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        bandeau_layout.setSpacing(0)  # Remove spacing

        # Set dark gray background for bandeau
        bandeau_widget = QWidget()
        bandeau_widget.setLayout(bandeau_layout)
        bandeau_widget.setFixedHeight(50)  # Set fixed height to match button height
        bandeau_widget.setStyleSheet("background-color: #2c3e50;")  # Dark gray background

        # StackedLayout pour basculer entre les vues
        self.stacked_layout = QStackedLayout()  # Initialize stacked_layout

        # Vue 1 : Liste des Dossiers
        self.dossiers_splitter = QSplitter(Qt.Horizontal)
        self.dossiers_splitter.setHandleWidth(0)  # Set handle width to 0 to remove the vertical gray bar

        # Liste scrollable des dossiers
        self.dossier_list = QListWidget()
        self.dossier_list.itemClicked.connect(self.load_dossier)
        self.dossier_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dossier_list.customContextMenuRequested.connect(self.show_context_menu)
        self.dossier_list.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.dossier_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrolling
        self.dossier_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)  # Enable smooth vertical scrolling
        self.dossier_list.setStyleSheet("""
            QListWidget {
                padding: 0px;
                margin: 0px;
                border: none;
            }
            QListWidget::item {
                white-space: nowrap; 
            }
        """)  # Ensure no margins, no border, and prevent horizontal overflow

        # Add "Créer un nouveau dossier" button at the bottom of the list
        self.new_dossier_button_bottom = QPushButton("Créer un nouveau dossier")
        self.new_dossier_button_bottom.setStyleSheet("""
            QPushButton {
                background-color: #0071a2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                margin: 10px;  
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.new_dossier_button_bottom.clicked.connect(self.new_dossier)

        # Create a layout for the left side
        left_layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Rechercher un dossier...")
        self.search_bar.textChanged.connect(self.filter_dossier_list)
        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(self.dossier_list)
        left_layout.addWidget(self.new_dossier_button_bottom)
        left_layout.setSpacing(10)  # Set spacing

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setStyleSheet("background-color: white;")  # Set background color to white
        self.dossiers_splitter.addWidget(left_widget)

        # Vue 2 : Formulaire et tableau des produits
        self.form_layout = QFormLayout()
        self.numero_dossier_input = QLineEdit()
        self.adresse_chantier_input = NoScrollComboBox()
        self.adresse_chantier_input.setEditable(True)
        addresses = get_addresses()
        self.adresse_chantier_input.addItem("")
        for addr in addresses:
            self.adresse_chantier_input.addItem(addr[1])
        self.libelle_travaux_input = QLineEdit()
        self.adresse_facturation_input = NoScrollComboBox()  # Change this line
        self.adresse_facturation_input.setEditable(True)     # Add this line
        addresses = get_addresses()
        self.adresse_facturation_input.addItem("")
        for addr in addresses:
            self.adresse_facturation_input.addItem(addr[1])  # Add addresses to combobox
        self.moyen_paiement_combo = NoScrollComboBox()
        self.moyen_paiement_combo.addItems(["Virement", "Espèces", "Chèque"])
        self.garantie_decennale_check = QCheckBox()
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description")
        self.description_input.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
                min-height: 100px;
            }
            QTextEdit:focus {
                border-color: #005980;
            }
        """)
        self.description_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Ensure the size policy is set correctly

        # Ajouter les champs au formulaire
        self.form_layout.addRow("Numéro de dossier :", self.numero_dossier_input)
        self.form_layout.addRow("Adresse chantier :", self.adresse_chantier_input)
        self.form_layout.addRow("Libellé travaux :", self.libelle_travaux_input)
        self.form_layout.addRow("Adresse facturation :", self.adresse_facturation_input)
        self.form_layout.addRow("Moyen de paiement :", self.moyen_paiement_combo)
        self.form_layout.addRow("Garantie décennale :", self.garantie_decennale_check)
        self.form_layout.addRow("Description :", self.description_input)

        self.save_button = QPushButton("Enregistrer")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.save_button.clicked.connect(self.save_dossier)

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 120px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.cancel_button.clicked.connect(self.cancel_editing)

        self.add_product_button = QPushButton("Ajouter un produit")
        self.add_product_button.clicked.connect(self.add_product)

        # Add buttons to a horizontal layout and align to the right
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.add_product_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        self.produits_table = QTableWidget()
        self.produits_table.setColumnCount(7)
        self.produits_table.setHorizontalHeaderLabels(["Désignation", "Prix Unitaire", "Quantité", "Unité", "Remise", "Total", ""])
        self.produits_table.setEditTriggers(QTableWidget.AllEditTriggers)
        
        # Set column widths
        self.produits_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Designation column stretches
        self.produits_table.setColumnWidth(1, 115)  # Prix Unitaire column narrower
        self.produits_table.setColumnWidth(2, 115)  # Quantité column narrower
        self.produits_table.setColumnWidth(3, 115)  # Unité column narrower
        self.produits_table.setColumnWidth(4, 115)  # Remise column narrower
        self.produits_table.setColumnWidth(5, 115)  # Total column narrower
        self.produits_table.setColumnWidth(6, 140)  # Delete button column width

        # Enable smooth scrolling
        self.produits_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.produits_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.generate_quote_button = QPushButton("Générer un devis")
        self.generate_quote_button.clicked.connect(self.generate_quote)
        self.generate_invoice_button = QPushButton("Générer une facture")
        self.generate_invoice_button.clicked.connect(self.show_invoice_type_dialog)
        self.edit_button = QPushButton("Modifier le dossier")
        self.edit_button.clicked.connect(self.enable_editing)

        self.form_widget = QWidget()
        form_layout = QVBoxLayout()
        
        # Créer un widget pour contenir le formulaire
        form_container = QWidget()
        form_container.setLayout(self.form_layout)
        form_layout.addWidget(form_container)
        
        # Ajouter les boutons au-dessus du tableau
        form_layout.addLayout(buttons_layout)
        
        # Configuration du tableau avec une taille minimale
        self.produits_table.setMinimumHeight(300)  # Hauteur minimale pour le tableau
        self.produits_table.verticalHeader().setDefaultSectionSize(40)  # Hauteur des lignes
        self.produits_table.setAlternatingRowColors(True)  # Lignes alternées pour meilleure lisibilité
        form_layout.addWidget(self.produits_table)
        
        # Créer un widget container pour les options
        self.options_container = QWidget()
        options_container_layout = QVBoxLayout()
        self.options_container.setLayout(options_container_layout)
        
        # Ajouter les widgets d'options au container
        self.options_label = QLabel("Options proposées :")
        options_container_layout.addWidget(self.options_label)
        
        self.options_table = QTableWidget()
        self.options_table.setColumnCount(7)
        self.options_table.setHorizontalHeaderLabels(["Désignation", "Prix Unitaire", "Quantité", "Unité", "Remise", "Total", ""])
        self.options_table.setEditTriggers(QTableWidget.AllEditTriggers)
        # Ajout du défilement fluide pour le tableau des options
        self.options_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.options_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Configuration identique au tableau des produits
        self.options_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Designation column stretches
        self.options_table.setColumnWidth(1, 115)  # Prix Unitaire column narrower
        self.options_table.setColumnWidth(2, 115)  # Quantité column narrower
        self.options_table.setColumnWidth(3, 115)  # Unité column narrower
        self.options_table.setColumnWidth(4, 115)  # Remise column narrower
        self.options_table.setColumnWidth(5, 115)  # Total column narrower
        self.options_table.setColumnWidth(6, 140)  # Delete button column width

        self.options_table.setMinimumHeight(200)
        self.options_table.verticalHeader().setDefaultSectionSize(40)
        self.options_table.setAlternatingRowColors(True)
        options_container_layout.addWidget(self.options_table)
        
        # Ajouter le container au form_layout
        form_layout.addWidget(self.options_container)
        
        # Ajouter le bouton d'options après le container (en dehors)
        self.add_option_button = QPushButton("Ajouter une option")
        self.add_option_button.clicked.connect(self.add_option)
        form_layout.addWidget(self.add_option_button)
        
        # Cacher le container par défaut
        self.options_container.hide()

        # Ajouter les cases à cocher "Devis signé" et "Facture payée"
        self.devis_signe_check = QCheckBox()
        self.facture_payee_check = QCheckBox()
        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.addStretch()
        checkboxes_layout.addWidget(QLabel("Devis signé :"))
        checkboxes_layout.addWidget(self.devis_signe_check)
        checkboxes_layout.addSpacing(150)  # Add space between checkboxes
        checkboxes_layout.addWidget(QLabel("Facture payée :"))
        checkboxes_layout.addWidget(self.facture_payee_check)
        checkboxes_layout.addStretch()
        
        # Add space above and below the checkboxes
        form_layout.addSpacing(20)
        form_layout.addLayout(checkboxes_layout)
        form_layout.addSpacing(20)

        # Ajouter les boutons de génération et d'édition
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addWidget(self.generate_quote_button)
        action_buttons_layout.addWidget(self.generate_invoice_button)
        action_buttons_layout.addWidget(self.edit_button)
        form_layout.addLayout(action_buttons_layout)

        # Créer un QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Mettre le form_widget dans le QScrollArea
        self.form_widget.setLayout(form_layout)
        self.scroll_area.setWidget(self.form_widget)
        
        # Ajouter le QScrollArea au splitter
        # Replace old self.dossiers_splitter.addWidget(self.scroll_area)
        # with a QStackedLayout for the right side
        self.right_stack = QStackedLayout()
        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_stack)
        self.dossiers_splitter.addWidget(self.right_widget)

        # Remove the following line:
        # self.main_layout.addWidget(self.no_dossier_label)

        # Instead, add no_dossier_label to the right stack
        self.no_dossier_label = QLabel("Sélectionnez un dossier")
        self.no_dossier_label.setAlignment(Qt.AlignCenter)
        self.no_dossier_label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        self.right_stack.addWidget(self.no_dossier_label)
        self.right_stack.addWidget(self.scroll_area)

        self.dossiers_splitter.setStretchFactor(0, 3)  
        self.dossiers_splitter.setStretchFactor(1, 6)  

        # Ajouter le splitter au stacked layout
        self.stacked_layout.addWidget(self.dossiers_splitter)

        # Vue 2 : Liste des Factures
        self.facture_view = ListeFacture()
        self.stacked_layout.addWidget(self.facture_view)

        # Vue 3 : Liste des Devis
        self.devis_view = ListeDevis()
        self.stacked_layout.addWidget(self.devis_view)

        # Vue 4 : Liste des Adresses
        self.adresses_view = ManageAddressesDialog()
        self.adresses_view.addresses_modified.connect(self.refresh_addresses)
        self.stacked_layout.addWidget(self.adresses_view)

        # Ajouter le bandeau et le contenu principal au layout principal
        self.main_layout.addWidget(bandeau_widget)  # Add bandeau_widget instead of bandeau_layout
        self.main_layout.addLayout(self.stacked_layout)
        self.setLayout(self.main_layout)

        self.load_dossiers()

        # Define styles for table widgets
        self.table_button_style = """
            QPushButton {
                background-color: #e74c3c;
                padding: 1px;
                min-width: 60px;
                color: white;
                border: none;
                border-radius: 3px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #ffffff;
            }
        """
        self.table_combo_style = """
            QComboBox {
                border: 1px solid #dcdcdc;
                border-radius: 0px;
                padding: 1px;
                background-color: none;
            }
            QComboBox::drop-down {
                border-left: 1px solid #dcdcdc;
                background-color: #ffffff;
            }
        """
        self.is_editing = False  # Track if the user is in edit mode
        self.quantity_options = ["", "Forfait", "Ensemble"]

        self.check_for_updates()
        
        # Initialiser le serveur local
        self._server = QLocalServer(self)
        self._server.listen("NMGFacturation")
        self._server.newConnection.connect(self._activate_window)

    def _activate_window(self):
        """Active la fenêtre quand une autre instance essaie de démarrer"""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
        self.raise_()

    def check_for_updates(self):
        """Vérifie si une mise à jour est disponible"""
        try:
            response = requests.get(f"{self.update_url}/check", timeout=5)
            if response.status_code == 200:
                update_info = response.json()
                if self._version_is_greater(update_info['version'], self.APP_VERSION):
                    self._prompt_update(update_info['version'])
        except Exception as e:
            print(f"Erreur lors de la vérification des mises à jour: {e}")
    
    def _version_is_greater(self, version_a, version_b):
        """Compare deux numéros de version"""
        try:
            a_parts = [int(x) for x in version_a.split('.')]
            b_parts = [int(x) for x in version_b.split('.')]
            
            # Comparer chaque partie de la version
            for i in range(max(len(a_parts), len(b_parts))):
                a = a_parts[i] if i < len(a_parts) else 0
                b = b_parts[i] if i < len(b_parts) else 0
                if a > b:
                    return True
                if b > a:
                    return False
            return False  # Versions égales
        except Exception as e:
            print(f"Erreur lors de la comparaison des versions: {e}")
            return False
        
    def _prompt_update(self, new_version):
        """Affiche le dialogue de mise à jour"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Mise à jour disponible")
        msg.setText(f"Une nouvelle version ({new_version}) est disponible !")
        msg.setInformativeText("Voulez-vous l'installer maintenant ?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText("Mettre à jour")
        msg.button(QMessageBox.No).setText("Plus tard")

        if msg.exec_() == QMessageBox.Yes:
            self._launch_updater(new_version)
            
    def _launch_updater(self, version):
        """Lance l'application de mise à jour"""
        try:
            updater_path = os.path.join(
                os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(),
                "NMGFacturationUpdater.exe"
            )
            if not os.path.exists(updater_path):
                QMessageBox.critical(self, "Erreur", "Programme de mise à jour non trouvé.")
                return
                
            # Lancer l'updater avant de quitter
            subprocess.Popen([updater_path, version])
            # Forcer la fermeture de l'application principale
            sys.exit(0)  
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du lancement de la mise à jour: {e}")

    def sanitize_input(self, text):
        return text.replace(',', '.')

    def format_decimal(self, value):
        return str(value).replace('.', ',')

    def load_dossiers(self):
        self.dossier_list.clear()
        dossiers = get_dossiers()
        
        # Convert dossiers to a list of tuples with parsed year and number
        sorted_dossiers = []
        for dossier in dossiers:
            numero = dossier[1]
            if '/' in numero:
                year, num = numero.split('/')
                sorted_dossiers.append((int(year), int(num), dossier))
        
        # Sort by year (descending) then by number (descending)
        sorted_dossiers.sort(key=lambda x: (-x[0], -x[1]))
        
        # Add sorted items to list
        for _, _, dossier in sorted_dossiers:
            self.dossier_list.addItem(f"{dossier[1]} - {dossier[3]}")
        
        self.show_select_message()

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)

    def save_dossier(self):
        try:
            numero_dossier = self.numero_dossier_input.text()
            adresse_chantier = self.adresse_chantier_input.currentText()
            libelle_travaux = self.libelle_travaux_input.text()
            adresse_facturation = self.adresse_facturation_input.currentText()
            moyen_paiement = self.moyen_paiement_combo.currentText()
            garantie_decennale = 1 if self.garantie_decennale_check.isChecked() else 0
            description = self.description_input.toPlainText()
            devis_signe = 1 if self.devis_signe_check.isChecked() else 0
            facture_payee = 1 if self.facture_payee_check.isChecked() else 0
            devis_generated = getattr(self, 'devis_generated', 0) # Récupère la valeur si existe
            facture_generated = getattr(self, 'facture_generated', 0)

            if not (numero_dossier and adresse_chantier):
                self.show_error_message("Erreur", "Veuillez remplir tous les champs obligatoires")
                return False

            if hasattr(self, 'current_dossier_id'):
                update_dossier(
                    self.current_dossier_id,
                    numero_dossier,
                    adresse_chantier,
                    libelle_travaux,
                    adresse_facturation,
                    moyen_paiement,
                    garantie_decennale,
                    description,
                    devis_signe,
                    facture_payee,
                    devis_generated,
                    facture_generated
                )
                dossier_id = self.current_dossier_id
            else:
                dossier_id = add_dossier(
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
                self.current_dossier_id = dossier_id
                self.devis_generated = 0 
                self.facture_generated = 0

            if not self.save_produits(dossier_id):
                return False
                
            if not self.save_options(dossier_id):
                return False

            self.disable_editing()  # Désactiver le mode édition
            
            # Mettre à jour la liste des dossiers
            self.load_dossiers()
            
            # Trouver et sélectionner le dossier dans la liste
            for i in range(self.dossier_list.count()):
                item = self.dossier_list.item(i)
                if item.text().startswith(f"{numero_dossier} -"):
                    self.dossier_list.setCurrentItem(item)
                    # Déclencher manuellement l'événement de clic pour charger le dossier
                    self.load_dossier(item)
                    break

            QMessageBox.information(self, "Succès", "Dossier sauvegardé avec succès")
            return True
            
        except ValueError:
            self.show_error_message("Erreur de saisie", "Veuillez entrer des valeurs numériques valides pour les champs numériques.")
            return False
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors de la sauvegarde des produits : {e}")
            return False

    def save_produits(self, dossier_id):
        try:
            new_produits = []
            for row in range(self.produits_table.rowCount()):
                designation = self.produits_table.item(row, 0).text()
                # Capitalize first letter of designation
                designation = designation[0].upper() + designation[1:] if designation else ""
                
                quantite = self.produits_table.cellWidget(row, 2).currentText()
                unite = self.produits_table.cellWidget(row, 3).currentText()
                unite = None if unite == "aucune" else unite
                prix = float(self.sanitize_input(self.produits_table.item(row, 1).text()))
                remise = float(self.sanitize_input(self.produits_table.item(row, 4).text()))
                if designation or quantite or prix != 0.0:
                    new_produits.append((designation, quantite, prix, remise, unite))

            delete_produits(dossier_id)
            for produit in new_produits:
                add_produit(dossier_id, *produit)
            return True
            
        except ValueError:
            self.show_error_message("Erreur de saisie", "Veuillez entrer des valeurs numériques valides pour les champs numériques.")
            return False
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors de la sauvegarde des produits : {e}")
            return False

    def save_options(self, dossier_id):
        try:
            new_options = []
            for row in range(self.options_table.rowCount()):
                designation = self.options_table.item(row, 0).text()
                # Capitalize first letter of designation
                designation = designation[0].upper() + designation[1:] if designation else ""
                
                quantite = self.options_table.cellWidget(row, 2).currentText()
                unite = self.options_table.cellWidget(row, 3).currentText()
                unite = None if unite == "aucune" else unite
                prix = float(self.sanitize_input(self.options_table.item(row, 1).text()))
                remise = float(self.sanitize_input(self.options_table.item(row, 4).text()))
                if designation or quantite or prix != 0.0:
                    new_options.append((designation, quantite, prix, remise, unite))

            delete_options(dossier_id)
            for option in new_options:
                add_option(dossier_id, *option)
            return True
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors de la sauvegarde des options : {e}")
            return False

    def load_dossier(self, item):
        if self.is_editing:
            previous_item = None
            # Trouver l'item précédemment sélectionné
            for i in range(self.dossier_list.count()):
                if self.dossier_list.item(i).text().startswith(f"{self.numero_dossier_input.text()} -"):
                    previous_item = self.dossier_list.item(i)
                    break
                    
            if not self.show_unsaved_changes_warning():
                # Si l'utilisateur ne veut pas perdre ses modifications,
                # on restaure la sélection précédente
                self.dossier_list.setCurrentItem(previous_item)
                return

        try:
            self.hide_select_message()
            dossier_text = item.text().split(" - ")
            numero_dossier = dossier_text[0]
            libelle_travaux = dossier_text[1]
            self.numero_dossier_input.setText(numero_dossier)
            self.libelle_travaux_input.setText(libelle_travaux)
            dossier_id = self.get_dossier_id(numero_dossier)
            self.current_dossier_id = dossier_id
            self.load_dossier_by_id(dossier_id)
            self.disable_editing()
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors du chargement du dossier : {e}")

    def load_dossier_by_id(self, dossier_id):
        try:
            dossier = self.get_dossier(dossier_id)
            self.numero_dossier_input.setText(dossier[1])
            self.adresse_chantier_input.setCurrentText(dossier[2])
            self.libelle_travaux_input.setText(dossier[3])
            self.moyen_paiement_combo.setCurrentText(dossier[5])
            self.garantie_decennale_check.setChecked(dossier[6] == 1)  
            self.description_input.setText(dossier[7])
            self.devis_signe_check.setChecked(dossier[8] == 1)  
            self.facture_payee_check.setChecked(dossier[9] == 1) 
            
            self.adresse_facturation_input.setCurrentText(dossier[4])
            
            # Modifier l'ordre des colonnes dans le tableau des produits
            produits = get_produits(dossier_id)
            self.produits_table.setRowCount(len(produits))
            for row, produit in enumerate(produits):
                designation_item = QTableWidgetItem(produit[2])
                prix_item = QTableWidgetItem(self.format_decimal(produit[4]))
                
                # Nouvelle combobox pour la quantité
                quantity_combo = self.create_quantity_combo()
                quantity_value = str(produit[3]) if produit[3] is not None else ""
                if quantity_value in self.quantity_options:
                    quantity_combo.setCurrentText(quantity_value)
                else:
                    quantity_combo.setCurrentText(quantity_value)
                
                # Configuration de l'unité
                unite = produit[6] if produit[6] is not None else "aucune"
                unite_combo = NoScrollComboBox()
                unite_combo.addItems(["aucune", "ml", "m²", "m³"])
                unite_combo.setCurrentText(unite)
                unite_combo.setFocusPolicy(Qt.NoFocus)
                unite_combo.setStyleSheet(self.table_combo_style)
                
                remise_item = QTableWidgetItem(self.format_decimal(produit[5]))
                prix_unitaire = produit[4]
                remise = produit[5]
                
                try:
                    if quantity_value and quantity_value not in ["Forfait", "Ensemble"]:
                        quantite_num = float(quantity_value.replace(',', '.'))
                        prix_total = (quantite_num * prix_unitaire) - remise
                    else:
                        prix_total = prix_unitaire - remise
                except (ValueError, TypeError):
                    prix_total = prix_unitaire - remise
                
                total_item = QTableWidgetItem(self.format_decimal(round(prix_total, 2)))
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                
                # Mise à jour de l'ordre des colonnes
                self.produits_table.setItem(row, 0, designation_item)
                self.produits_table.setItem(row, 1, prix_item)
                self.produits_table.setCellWidget(row, 2, quantity_combo)
                self.produits_table.setCellWidget(row, 3, unite_combo)
                self.produits_table.setItem(row, 4, remise_item)
                self.produits_table.setItem(row, 5, total_item)
                
                delete_button = QPushButton("Supprimer")
                delete_button.setStyleSheet(self.table_button_style)
                delete_button.clicked.connect(lambda _, r=row: self.delete_product(r))
                self.produits_table.setCellWidget(row, 6, delete_button)
            
            # Même logique pour les options
            options = get_options(dossier_id)
            
            # Afficher ou cacher le container des options selon s'il y en a ou non
            self.options_container.setVisible(bool(options))
            
            if options:
                self.options_table.setRowCount(len(options))
                for row, option in enumerate(options):
                    # Même logique que pour les produits
                    designation_item = QTableWidgetItem(option[2])
                    prix_item = QTableWidgetItem(self.format_decimal(option[4]))
                    
                    quantity_combo = self.create_quantity_combo()
                    quantity_combo.setEditMode(self.is_editing)
                    quantity_value = str(option[3]) if option[3] is not None else ""
                    if quantity_value in self.quantity_options:
                        quantity_combo.setCurrentText(quantity_value)
                    else:
                        quantity_combo.setCurrentText(quantity_value)
                    
                    unite = option[6] if option[6] is not None else "aucune"
                    unite_combo = NoScrollComboBox()
                    unite_combo.addItems(["aucune", "ml", "m²", "m³"])
                    unite_combo.setCurrentText(unite)
                    unite_combo.setFocusPolicy(Qt.NoFocus)
                    unite_combo.setStyleSheet(self.table_combo_style)
                    
                    remise_item = QTableWidgetItem(self.format_decimal(option[5]))
                    prix_unitaire = option[4]
                    remise = option[5]
                    
                    # Nouveau calcul du prix total pour les options
                    try:
                        if quantity_value and quantity_value not in ["Forfait", "Ensemble"]:
                            quantite_num = float(quantity_value.replace(',', '.'))
                            prix_total = (quantite_num * prix_unitaire) - remise
                        else:
                            prix_total = prix_unitaire - remise
                    except (ValueError, TypeError):
                        prix_total = prix_unitaire - remise
                    
                    total_item = QTableWidgetItem(self.format_decimal(round(prix_total, 2)))
                    total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                    
                    # Mise à jour de l'ordre des colonnes
                    self.options_table.setItem(row, 0, designation_item)
                    self.options_table.setItem(row, 1, prix_item)
                    self.options_table.setCellWidget(row, 2, quantity_combo)
                    self.options_table.setCellWidget(row, 3, unite_combo)
                    self.options_table.setItem(row, 4, remise_item)
                    self.options_table.setItem(row, 5, total_item)
                    
                    delete_button = QPushButton("Supprimer")
                    delete_button.setStyleSheet(self.table_button_style)
                    delete_button.clicked.connect(lambda _, r=row: self.delete_option(r))
                    self.options_table.setCellWidget(row, 6, delete_button)
                
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors du chargement des détails du dossier : {e}")

    def get_dossier_id(self, numero_dossier):
        dossiers = get_dossiers()
        for dossier in dossiers:
            if dossier[1] == numero_dossier:
                return dossier[0]
        return None

    def get_dossier(self, dossier_id):
        dossiers = get_dossiers()
        for dossier in dossiers:
            if dossier[0] == dossier_id:
                return dossier
        return None

    @pyqtSlot()
    def new_dossier(self):
        if self.is_editing and not self.show_unsaved_changes_warning():
            return
        self.hide_select_message()
        # Effacer tous les champs
        self.numero_dossier_input.setText(generate_next_dossier_number())  # Modifier cette ligne
        self.adresse_chantier_input.setCurrentIndex(0)
        self.libelle_travaux_input.clear()
        self.adresse_facturation_input.setCurrentIndex(0)
        self.moyen_paiement_combo.setCurrentIndex(0)
        self.garantie_decennale_check.setChecked(False)
        self.description_input.clear()
        self.devis_signe_check.setChecked(False)
        self.facture_payee_check.setChecked(False)
        self.produits_table.setRowCount(0)
        
        if hasattr(self, 'current_dossier_id'):
            del self.current_dossier_id

        # Désélectionner l'élément sélectionné dans la liste des dossiers
        self.dossier_list.clearSelection()
    
        # Ajouter les produits obligatoires
        produits_obligatoires = [
            "Acheminement matériel",
            "Déplacement",
            "Néttoyage chantier",
            "Mise en déchetterie payante"
        ]
        for produit in produits_obligatoires:
            row_position = self.produits_table.rowCount()
            self.produits_table.insertRow(row_position)
            self.produits_table.setItem(row_position, 0, QTableWidgetItem(produit))
            
            # Nouvelle combobox pour la quantité
            quantity_combo = self.create_quantity_combo()
            self.produits_table.setCellWidget(row_position, 2, quantity_combo)
            
            unite_combo = NoScrollComboBox()
            unite_combo.addItems(["aucune", "ml", "m²", "m³"])
            unite_combo.setFocusPolicy(Qt.NoFocus)
            unite_combo.setStyleSheet(self.table_combo_style)
            self.produits_table.setCellWidget(row_position, 3, unite_combo)
            self.produits_table.setItem(row_position, 1, QTableWidgetItem("0,0"))
            self.produits_table.setItem(row_position, 4, QTableWidgetItem("0,0"))
            prix_total_item = QTableWidgetItem("0,0")
            prix_total_item.setFlags(prix_total_item.flags() & ~Qt.ItemIsEditable)
            self.produits_table.setItem(row_position, 5, prix_total_item)
            
            # Ajouter le bouton de suppression
            delete_button = QPushButton("Supprimer")
            delete_button.setStyleSheet(self.table_button_style)
            delete_button.clicked.connect(lambda _, r=row_position: self.delete_product(r))
            self.produits_table.setCellWidget(row_position, 6, delete_button)
        
        # Cacher le container des options pour un nouveau dossier
        self.options_container.hide()
        self.options_table.setRowCount(0)
        
        self.enable_editing()  # Switch to editable view

    def create_quantity_combo(self):
        """Crée une combobox non scrollable pour la quantité"""
        combo = NoScrollQuantityComboBox()
        combo.addItems(self.quantity_options)
        combo.setStyleSheet(self.table_combo_style)
        combo.setFocusPolicy(Qt.StrongFocus)
        combo._enabled = False  # S'assurer que c'est désactivé par défaut
        return combo

    def add_product(self):
        row_position = self.produits_table.rowCount()
        self.produits_table.insertRow(row_position)
        self.produits_table.setItem(row_position, 0, QTableWidgetItem(""))
        
        # Nouvelle combobox pour la quantité
        quantity_combo = self.create_quantity_combo()
        quantity_combo.setEditMode(True)  # Activer l'édition immédiatement
        self.produits_table.setCellWidget(row_position, 2, quantity_combo)
        
        unite_combo = NoScrollComboBox()
        unite_combo.addItems(["aucune", "ml", "m²", "m³"])
        unite_combo.setFocusPolicy(Qt.NoFocus)
        unite_combo.setStyleSheet(self.table_combo_style)
        self.produits_table.setCellWidget(row_position, 3, unite_combo)
        
        self.produits_table.setItem(row_position, 1, QTableWidgetItem("0,0"))
        self.produits_table.setItem(row_position, 4, QTableWidgetItem("0,0"))
        prix_total_item = QTableWidgetItem("0,0")
        prix_total_item.setFlags(prix_total_item.flags() & ~Qt.ItemIsEditable)
        self.produits_table.setItem(row_position, 5, prix_total_item)
        
        delete_button = QPushButton("Supprimer")
        delete_button.setStyleSheet(self.table_button_style)
        delete_button.clicked.connect(lambda _, r=row_position: self.delete_product(r))
        self.produits_table.setCellWidget(row_position, 6, delete_button)

        # Set focus to the "Désignation" input of the new row
        self.produits_table.setCurrentCell(row_position, 0)
        self.produits_table.editItem(self.produits_table.item(row_position, 0))

    def delete_product(self, row):
        self.produits_table.removeRow(row)
        # Update delete buttons to ensure correct row indices
        for row in range(self.produits_table.rowCount()):
            delete_button = QPushButton("Supprimer")
            delete_button.setStyleSheet(self.table_button_style)
            delete_button.clicked.connect(lambda _, r=row: self.delete_product(r))
            self.produits_table.setCellWidget(row, 6, delete_button)

    def add_option(self):
        row_position = self.options_table.rowCount()
        self.options_table.insertRow(row_position)
        self.options_table.setItem(row_position, 0, QTableWidgetItem(""))
        
        # Nouvelle combobox pour la quantité
        quantity_combo = self.create_quantity_combo()
        quantity_combo.setEditMode(self.is_editing)  # Ajoutez cette ligne
        self.options_table.setCellWidget(row_position, 2, quantity_combo)
        
        unite_combo = NoScrollComboBox()
        unite_combo.addItems(["aucune", "ml", "m²", "m³"])
        unite_combo.setFocusPolicy(Qt.NoFocus)
        unite_combo.setStyleSheet(self.table_combo_style)
        self.options_table.setCellWidget(row_position, 3, unite_combo)
        
        self.options_table.setItem(row_position, 1, QTableWidgetItem("0,0"))
        self.options_table.setItem(row_position, 4, QTableWidgetItem("0,0"))
        prix_total_item = QTableWidgetItem("0,0")
        prix_total_item.setFlags(prix_total_item.flags() & ~Qt.ItemIsEditable)
        self.options_table.setItem(row_position, 5, prix_total_item)
        
        delete_button = QPushButton("Supprimer")
        delete_button.setStyleSheet(self.table_button_style)
        delete_button.clicked.connect(lambda _, r=row_position: self.delete_option(r))
        self.options_table.setCellWidget(row_position, 6, delete_button)
        
        # Montrer le container des options quand on ajoute la première option
        self.options_container.show()

        # Ajouter l'auto-focus sur la case désignation
        self.options_table.setCurrentCell(row_position, 0)
        self.options_table.editItem(self.options_table.item(row_position, 0))

    def delete_option(self, row):
        self.options_table.removeRow(row)
        for row in range(self.options_table.rowCount()):
            delete_button = QPushButton("Supprimer")
            delete_button.setStyleSheet(self.table_button_style)
            delete_button.clicked.connect(lambda _, r=row: self.delete_option(r))
            self.options_table.setCellWidget(row, 6, delete_button)

    def generate_quote(self):
        try:
            if hasattr(self, 'current_dossier_id'):
                # Importer et appeler directement la fonction
                from src.utils.generate_devis import generate_devis
                if generate_devis(self.current_dossier_id):
                    QMessageBox.information(self, "Devis", "Devis généré avec succès")
                    update_document_generated(self.current_dossier_id, 'devis', True)
                    self.devis_generated = 1
                else:
                    # Ne rien faire si l'utilisateur a annulé
                    pass
            else:
                self.show_error_message("Erreur", "Aucun dossier sélectionné")
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite : {e}")

    def show_invoice_type_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Type de Facture")
        layout = QVBoxLayout()

        label = QLabel("Sélectionnez le type de facture:")
        layout.addWidget(label)

        self.invoice_type_combo = NoScrollComboBox()
        self.invoice_type_combo.addItems(["Facture classique", "Facture aquittée", "Facture d'acompte", "Facture définitive"])
        layout.addWidget(self.invoice_type_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("OK")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(lambda: self.generate_invoice(dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec_()

    def generate_invoice(self, dialog):
        invoice_type = self.invoice_type_combo.currentText()
        dialog.accept()
        try:
            if hasattr(self, 'current_dossier_id'):
                # Importer et appeler directement la fonction
                from src.utils.generate_facture import generate_facture
                if generate_facture(self.current_dossier_id, invoice_type):
                    QMessageBox.information(self, "Facture", f"{invoice_type} générée avec succès")
                    update_document_generated(self.current_dossier_id, 'facture', True)
                    self.facture_generated = 1
            else:
                # Ne rien faire si l'utilisateur a annulé
                pass
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite : {e}")

    def enable_editing(self):
        self.is_editing = True
        self.numero_dossier_input.setReadOnly(False)
        self.adresse_chantier_input.setEnabled(True)  # Enable QComboBox in edit mode
        self.libelle_travaux_input.setReadOnly(False)
        self.adresse_facturation_input.setEnabled(True)  # Update this line
        self.moyen_paiement_combo.setEnabled(True)
        self.garantie_decennale_check.setEnabled(True)
        self.devis_signe_check.setEnabled(True)  # Enable checkbox in edit mode
        self.facture_payee_check.setEnabled(True)  # Enable checkbox in edit mode
        self.description_input.setReadOnly(False)
        self.produits_table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.options_table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.save_button.setEnabled(True)
        self.add_product_button.setEnabled(True)
        self.add_option_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.save_button.show()
        self.add_product_button.show()
        self.add_option_button.show()
        self.cancel_button.show()
        self.generate_quote_button.setEnabled(False)
        self.generate_invoice_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        
        # Enable delete buttons and unit combo boxes
        for row in range(self.produits_table.rowCount()):
            delete_button = self.produits_table.cellWidget(row, 6)
            if delete_button:
                delete_button.setEnabled(True)
            unite_combo = self.produits_table.cellWidget(row, 3)
            if unite_combo:
                unite_combo.setEnabled(True)
            quantity_combo = self.produits_table.cellWidget(row, 2)
            if quantity_combo:
                quantity_combo.setEditMode(True)
                
        for row in range(self.options_table.rowCount()):
            delete_button = self.options_table.cellWidget(row, 6)
            if delete_button:
                delete_button.setEnabled(True)
            unite_combo = self.options_table.cellWidget(row, 3)
            if unite_combo:
                unite_combo.setEnabled(True)
            quantity_combo = self.options_table.cellWidget(row, 2)
            if quantity_combo:
                quantity_combo.setEditMode(True)

    def disable_editing(self):
        self.is_editing = False
        self.numero_dossier_input.setReadOnly(True)
        self.adresse_chantier_input.setEnabled(False)  # Disable QComboBox in non-edit mode
        self.libelle_travaux_input.setReadOnly(True)
        self.adresse_facturation_input.setEnabled(False)  # Update this line
        self.moyen_paiement_combo.setEnabled(False)
        self.garantie_decennale_check.setEnabled(False)
        self.devis_signe_check.setEnabled(False)  # Disable checkbox in non-edit mode
        self.facture_payee_check.setEnabled(False)  # Disable checkbox in non-edit mode
        self.description_input.setReadOnly(True)
        self.produits_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.options_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.save_button.setEnabled(False)
        self.add_product_button.setEnabled(False)
        self.add_option_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.save_button.hide()
        self.add_product_button.hide()
        self.add_option_button.hide()
        self.cancel_button.hide()
        self.generate_quote_button.setEnabled(True)
        self.generate_invoice_button.setEnabled(True)
        self.edit_button.setEnabled(True)
        
        # Disable delete buttons and unit combo boxes
        for row in range(self.produits_table.rowCount()):
            delete_button = self.produits_table.cellWidget(row, 6)
            if delete_button:
                delete_button.setEnabled(False)
            unite_combo = self.produits_table.cellWidget(row, 3)
            if unite_combo:
                unite_combo.setEnabled(False)
            quantity_combo = self.produits_table.cellWidget(row, 2)
            if quantity_combo:
                quantity_combo.setEditMode(False)
                
        for row in range(self.options_table.rowCount()):
            delete_button = self.options_table.cellWidget(row, 6)
            if delete_button:
                delete_button.setEnabled(False)
            unite_combo = self.options_table.cellWidget(row, 3)
            if unite_combo:
                unite_combo.setEnabled(False)
            quantity_combo = self.options_table.cellWidget(row, 2)
            if quantity_combo:
                quantity_combo.setEditMode(False)

    def show_context_menu(self, position):
        menu = QMenu()
        delete_action = menu.addAction("Supprimer le dossier")
        delete_action.triggered.connect(self.delete_selected_dossier)
        menu.exec_(self.dossier_list.viewport().mapToGlobal(position))

    def delete_selected_dossier(self):
        selected_item = self.dossier_list.currentItem()
        if selected_item:
            dossier_text = selected_item.text().split(" - ")
            numero_dossier = dossier_text[0]
            dossier_id = self.get_dossier_id(numero_dossier)
            if dossier_id:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setWindowTitle('Confirmation')
                msg_box.setText('Êtes-vous sûr de vouloir supprimer ce dossier?')
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                yes_button = msg_box.button(QMessageBox.Yes)
                yes_button.setText("Oui")
                no_button = msg_box.button(QMessageBox.No)
                no_button.setText("Non")
                reply = msg_box.exec_()
                if reply == QMessageBox.Yes:
                    delete_dossier(dossier_id)
                    self.load_dossiers()

    def cancel_editing(self):
        """Cancel the editing and reload the current dossier details."""
        if hasattr(self, 'current_dossier_id'):
            self.load_dossier_by_id(self.current_dossier_id)
        else:
            # Si c'est un nouveau dossier (pas de current_dossier_id)
            self.show_select_message()  # Afficher le message "Sélectionnez un dossier"
            self.dossier_list.clearSelection()  # Déselectionner tout dossier dans la liste
        
        self.disable_editing()
        self.clear_focus()

    def clear_focus(self):
        """Clear focus from all input fields."""
        self.setFocus()

    def show_unsaved_changes_warning(self):
        """Show a warning message if there are unsaved changes."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('Modifications non enregistrées')
        msg_box.setText('Vous avez des modifications non enregistrées. Voulez-vous vraiment quitter sans enregistrer ?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Oui")
        no_button = msg_box.button(QMessageBox.No)
        no_button.setText("Non")
        reply = msg_box.exec_()
        if reply == QMessageBox.Yes:
            self.is_editing = False
            return True
        return reply == QMessageBox.Yes

    def closeEvent(self, event):
        """Handle the window close event."""
        if self.is_editing:
            if self.show_unsaved_changes_warning():
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def show_factures(self):
        if self.is_editing and not self.show_unsaved_changes_warning():
            return
        self.facture_view.load_factures()
        self.stacked_layout.setCurrentWidget(self.facture_view)
        self.dossiers_button.setStyleSheet(self.get_button_style(False))
        self.factures_button.setStyleSheet(self.get_button_style(True))
        self.devis_button.setStyleSheet(self.get_button_style(False))
        self.adresses_button.setStyleSheet(self.get_button_style(False))

    def show_devis(self):
        if self.is_editing and not self.show_unsaved_changes_warning():
            return
        self.devis_view.load_devis()
        self.stacked_layout.setCurrentWidget(self.devis_view)
        self.dossiers_button.setStyleSheet(self.get_button_style(False))
        self.factures_button.setStyleSheet(self.get_button_style(False))
        self.devis_button.setStyleSheet(self.get_button_style(True))
        self.adresses_button.setStyleSheet(self.get_button_style(False))

    def show_dossiers(self):
        if self.is_editing and not self.show_unsaved_changes_warning():
            return
        self.load_dossiers()
        self.refresh_addresses()
        self.stacked_layout.setCurrentWidget(self.dossiers_splitter)
        self.dossiers_button.setStyleSheet(self.get_button_style(True))
        self.factures_button.setStyleSheet(self.get_button_style(False))
        self.devis_button.setStyleSheet(self.get_button_style(False))
        self.adresses_button.setStyleSheet(self.get_button_style(False))

    def show_addresses(self):
        if self.is_editing and not self.show_unsaved_changes_warning():
            return
        self.adresses_view.load_addresses()
        self.stacked_layout.setCurrentWidget(self.adresses_view)
        self.dossiers_button.setStyleSheet(self.get_button_style(False))
        self.factures_button.setStyleSheet(self.get_button_style(False))
        self.devis_button.setStyleSheet(self.get_button_style(False))
        self.adresses_button.setStyleSheet(self.get_button_style(True))

    def get_button_style(self, active):
        if (active):
            return """
                QPushButton {
                    background-color: rgb(79, 93, 107);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    min-width: 150px;
                    max-width: 150px;
                    font-size: 14px;
                    height: 50px;  
                    border-left: 1px solid #dcdcdc;  
                    border-radius: 0px;  
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
                QPushButton:pressed {
                    background-color: #2c3e50;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #2c3e50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    min-width: 150px;
                    max-width: 150px;
                    font-size: 14px;
                    height: 50px;  
                    border-left: 1px solid #dcdcdc;  
                    border-radius: 0px;  
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
                QPushButton:pressed {
                    background-color: #2c3e50;
                }
                QPushButton:disabled {
                    background-color: #bdc3c7;
                }
            """

    def show_select_message(self):
        self.right_stack.setCurrentWidget(self.no_dossier_label)

    def hide_select_message(self):
        self.right_stack.setCurrentWidget(self.scroll_area)

    def filter_dossier_list(self, query):
        query = query.lower()
        for row in range(self.dossier_list.count()):
            item = self.dossier_list.item(row)
            item.setHidden(query not in item.text().lower())

    def refresh_addresses(self):
        """Update both address comboboxes when addresses are modified"""
        # Save current selections
        current_chantier = self.adresse_chantier_input.currentText()
        current_facturation = self.adresse_facturation_input.currentText()
        
        # Clear and refill both comboboxes
        self.adresse_chantier_input.clear()
        self.adresse_facturation_input.clear()
        
        self.adresse_chantier_input.addItem("")
        self.adresse_facturation_input.addItem("")
        
        addresses = get_addresses()
        for addr in addresses:
            self.adresse_chantier_input.addItem(addr[1])
            self.adresse_facturation_input.addItem(addr[1])
        
        # Restore previous selections if they still exist
        index_chantier = self.adresse_chantier_input.findText(current_chantier)
        if index_chantier >= 0:
            self.adresse_chantier_input.setCurrentIndex(index_chantier)
            
        index_facturation = self.adresse_facturation_input.findText(current_facturation)
        if index_facturation >= 0:
            self.adresse_facturation_input.setCurrentIndex(index_facturation)

    def show_backup_dialog(self):
        if self.is_editing:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('Modifications non enregistrées')
            msg_box.setText("Vous devez d'abord enregistrer les modifications avant d'effectuer une sauvegarde")
            msg_box.setStandardButtons(QMessageBox.Ok)
            ok_button = msg_box.button(QMessageBox.Ok)
            ok_button.setText("OK")
            msg_box.exec_()
            return
        dialog = BackupDialog(self)
        dialog.exec_()

def get_last_dossier_number():
    try:
        dossiers = get_dossiers()
        current_year = datetime.datetime.now().year
        year_numbers = []
        
        for dossier in dossiers:
            numero = dossier[1]  # Get dossier number
            if '/' in numero:
                year, num = numero.split('/')
                if int(year) == current_year:
                    year_numbers.append(int(num))
        
        # Sort numbers to find gaps
        year_numbers.sort()
        
        # Find first gap in sequence
        for i in range(1, max(year_numbers) + 2 if year_numbers else 2):
            if i not in year_numbers:
                return i - 1  # Return number before gap
                
        return 0
    except:
        return 0

def generate_next_dossier_number():
    current_year = datetime.datetime.now().year
    last_number = get_last_dossier_number()
    next_number = last_number + 1
    return f"{current_year}/{next_number}"

if __name__ == "__main__":
    try:
        # Enable DPI scaling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        app = QApplication(sys.argv)
        
        # Vérifier si une instance est déjà en cours d'exécution
        if is_app_running():
            sys.exit(0)
            
        # Set modern font
        font = QFont("Segoe UI", 12)
        app.setFont(font)

        # Apply stylesheet
        app.setStyleSheet(load_stylesheet())

        # Vérifier/initialiser la base de données avant de lancer l'application
        if not initialize_database():
            sys.exit(1)

        # Créer les tables si la base de données existe
        create_tables()
        
        window = MainWindow()
        window.show()

        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Critical Error", str(e))
        sys.exit(1)