import sys
import os
import subprocess
import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QFormLayout, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QLabel, QStackedLayout, QHeaderView, QSplitter, QComboBox, QCheckBox, QScrollArea, QTextEdit, QMenu, QDialog, QDialogButtonBox, QSizePolicy, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFontDatabase, QFont, QIcon, QPalette, QColor
from PyQt5.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QLabel, 
                            QPushButton, QApplication)

# Corriger les imports pour utiliser les chemins complets
from src.database.database import (
    create_tables, 
    add_dossier, 
    get_dossiers, 
    get_produits, 
    add_produit, 
    update_dossier, 
    delete_produits, 
    delete_dossier, 
    add_option, 
    delete_options, 
    get_options
)
from src.views.liste_facture import ListeFacture
from src.views.liste_devis import ListeDevis

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
        else:
            # Si l'application est en développement
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
        return os.path.join(base_path, 'assets', relative_path)
    except Exception as e:
        print(f"Erreur lors de la récupération du chemin de la ressource : {e}")
        return None

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
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

def initialize_database():
    """Initialise ou vérifie la base de données"""
    db_path = os.path.join(os.environ['LOCALAPPDATA'], 'NMGFacturation', 'facturation.db')
    
    if not os.path.exists(db_path) or not verify_database():
        dialog = DatabaseWarningDialog()
        if dialog.exec_() == QDialog.Accepted:
            try:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
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

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

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
        self.bandeau_label = QLabel("Gestionnaire de facturation")
        self.bandeau_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.bandeau_label.setStyleSheet("color: white; padding: 10px;")
        
        self.dossiers_button = QPushButton("Liste des Dossiers")
        self.dossiers_button.setStyleSheet(self.get_button_style(True))
        self.dossiers_button.clicked.connect(self.show_dossiers)

        self.factures_button = QPushButton("Liste des Factures")
        self.factures_button.setStyleSheet(self.get_button_style(False))
        self.factures_button.clicked.connect(self.show_factures)

        self.devis_button = QPushButton("Liste des Devis")
        self.devis_button.setStyleSheet(self.get_button_style(False))
        self.devis_button.clicked.connect(self.show_devis)

        bandeau_layout.addWidget(self.bandeau_label)
        bandeau_layout.addWidget(self.dossiers_button)
        bandeau_layout.addWidget(self.factures_button)
        bandeau_layout.addWidget(self.devis_button)
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
        self.adresse_chantier_input.addItems([
            "",  # Empty first value
            "12 Av Henri Isnard - 06140 Vence", 
            "60 Av de Verdun - 06800 Cagne-sur-Mer", 
            "9 Av Thiers - 06130 Grasse",
            "7 Avenue de Grande Bretagne - 98000 Monaco",
            "1225 Route de la Fénerie - 06580 Pégomas",
            "23 Av Mont Fleury - 06300 Nice",
            "38 Bd de l'Esterel - 06150 Cannes La Bocca",
            "1544 Corniche d'Agrimont - 06700 Saint-Laurent-du-Var",
            "342 Chemin du Château d'Eau - 06610 La Gaude",
            "67 Bd Sadi Carnot - 06110 Le Cannet",
            "55 Bd Marechal Juin - 06800 Cagne-sur-Mer"
        ])
        self.libelle_travaux_input = QLineEdit()
        self.adresse_facturation_input = NoScrollComboBox()
        self.adresse_facturation_input.addItems([
            "Identique à l'adresse chantier", 
            "Autre"
        ])
        self.adresse_facturation_input.currentIndexChanged.connect(self.toggle_adresse_facturation)
        self.adresse_facturation_custom_input = QLineEdit()
        self.adresse_facturation_custom_input.setVisible(False)
        self.acompte_demande_input = QLineEdit()
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
        self.form_layout.addRow("", self.adresse_facturation_custom_input)
        self.form_layout.addRow("Acompte demandé (%) :", self.acompte_demande_input)
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
        self.produits_table.setHorizontalHeaderLabels(["Désignation", "Quantité", "Unité", "Prix Unitaire", "Remise", "Total", ""])
        self.produits_table.setEditTriggers(QTableWidget.AllEditTriggers)
        
        # Set column widths
        self.produits_table.setColumnWidth(0, 300)  # Désignation column wider
        self.produits_table.setColumnWidth(1, 100)  # Quantité column narrower
        self.produits_table.setColumnWidth(2, 100)  # Unité column narrower
        self.produits_table.setColumnWidth(3, 115)  # Prix Unitaire column narrower
        self.produits_table.setColumnWidth(4, 100)  # Remise column narrower
        self.produits_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.produits_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.produits_table.horizontalHeader().setStretchLastSection(True)

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
        self.options_table.setHorizontalHeaderLabels(["Désignation", "Quantité", "Unité", "Prix Unitaire", "Remise", "Total", ""])
        self.options_table.setEditTriggers(QTableWidget.AllEditTriggers)
        
        # Configuration identique au tableau des produits
        self.options_table.setColumnWidth(0, 300)
        self.options_table.setColumnWidth(1, 100)
        self.options_table.setColumnWidth(2, 100)
        self.options_table.setColumnWidth(3, 115)
        self.options_table.setColumnWidth(4, 100)
        self.options_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.options_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
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

    def sanitize_input(self, text):
        return text.replace(',', '.')

    def format_decimal(self, value):
        return str(value).replace('.', ',')

    def load_dossiers(self):
        self.dossier_list.clear()
        dossiers = get_dossiers()
        for dossier in dossiers:
            self.dossier_list.addItem(f"{dossier[1]} - {dossier[3]}")
        self.show_select_message()

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)

    def save_dossier(self):
        try:
            numero_dossier = self.numero_dossier_input.text()
            adresse_chantier = self.adresse_chantier_input.currentText()
            libelle_travaux = self.libelle_travaux_input.text()
            if self.adresse_facturation_input.currentIndex() == 0:
                adresse_facturation = self.adresse_chantier_input.currentText()
            else:
                adresse_facturation = self.adresse_facturation_custom_input.text()
            acompte_demande = float(self.sanitize_input(self.acompte_demande_input.text()) or 0)
            moyen_paiement = self.moyen_paiement_combo.currentText()
            garantie_decennale = 1 if self.garantie_decennale_check.isChecked() else 0
            description = self.description_input.toPlainText()
            devis_signe = 1 if self.devis_signe_check.isChecked() else 0
            facture_payee = 1 if self.facture_payee_check.isChecked() else 0

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
                    acompte_demande,
                    moyen_paiement,
                    garantie_decennale,
                    description,
                    devis_signe,
                    facture_payee
                )
                dossier_id = self.current_dossier_id
            else:
                dossier_id = add_dossier(
                    numero_dossier,
                    adresse_chantier,
                    libelle_travaux,
                    adresse_facturation,
                    acompte_demande,
                    moyen_paiement,
                    garantie_decennale,
                    description,
                    devis_signe,
                    facture_payee
                )
                self.current_dossier_id = dossier_id

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
                quantite = float(self.sanitize_input(self.produits_table.item(row, 1).text()))
                unite = self.produits_table.cellWidget(row, 2).currentText()
                unite = None if unite == "aucune" else unite
                prix = float(self.sanitize_input(self.produits_table.item(row, 3).text()))
                remise = float(self.sanitize_input(self.produits_table.item(row, 4).text()))
                if designation or quantite != 0 or prix != 0.0:
                    new_produits.append((designation, quantite, prix, remise, unite))

            # Delete old products first
            delete_produits(dossier_id)

            # Add new products
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
                quantite = float(self.sanitize_input(self.options_table.item(row, 1).text()))
                unite = self.options_table.cellWidget(row, 2).currentText()
                unite = None if unite == "aucune" else unite
                prix = float(self.sanitize_input(self.options_table.item(row, 3).text()))
                remise = float(self.sanitize_input(self.options_table.item(row, 4).text()))
                if designation or quantite != 0 or prix != 0.0:
                    new_options.append((designation, quantite, prix, remise, unite))

            delete_options(dossier_id)
            for option in new_options:
                add_option(dossier_id, *option)
            return True
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors de la sauvegarde des options : {e}")
            return False

    def load_dossier(self, item):
        if self.is_editing and not self.show_unsaved_changes_warning():
            return
        try:
            self.hide_select_message()
            dossier_text = item.text().split(" - ")
            numero_dossier = dossier_text[0]
            libelle_travaux = dossier_text[1]
            self.numero_dossier_input.setText(numero_dossier)
            self.libelle_travaux_input.setText(libelle_travaux)
            # Charger les détails du dossier
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
            self.acompte_demande_input.setText(self.format_decimal(dossier[5]))
            self.moyen_paiement_combo.setCurrentText(dossier[6])
            self.garantie_decennale_check.setChecked(bool(int(dossier[7])))
            self.description_input.setText(dossier[8])
            self.devis_signe_check.setChecked(bool(int(dossier[9])))
            self.facture_payee_check.setChecked(bool(int(dossier[10])))
            
            if dossier[4] == self.adresse_chantier_input.currentText():
                self.adresse_facturation_input.setCurrentIndex(0)
                self.adresse_facturation_custom_input.setVisible(False)
            else:
                self.adresse_facturation_input.setCurrentIndex(1)
                self.adresse_facturation_custom_input.setText(dossier[4])
                self.adresse_facturation_custom_input.setVisible(True)
            
            # Charger les produits associés au dossier
            produits = get_produits(dossier_id)
            self.produits_table.setRowCount(len(produits))
            for row, produit in enumerate(produits):
                designation_item = QTableWidgetItem(produit[2])
                quantite_item = QTableWidgetItem(self.format_decimal(produit[3]))
                prix_item = QTableWidgetItem(self.format_decimal(produit[4]))
                remise_item = QTableWidgetItem(self.format_decimal(produit[5]))
                prix_unitaire = produit[4]
                remise = produit[5]
                prix_total = (produit[3] * prix_unitaire) - remise
                total_item = QTableWidgetItem(self.format_decimal(round(prix_total, 2)))
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                self.produits_table.setItem(row, 0, designation_item)
                self.produits_table.setItem(row, 1, quantite_item)
                unite = produit[6] if produit[6] is not None else "aucune"
                unite_combo = NoScrollComboBox()
                unite_combo.addItems(["aucune", "m", "m²", "m³"])
                unite_combo.setCurrentText(unite)
                unite_combo.setFocusPolicy(Qt.NoFocus)
                unite_combo.setStyleSheet(self.table_combo_style)
                self.produits_table.setCellWidget(row, 2, unite_combo)
                self.produits_table.setItem(row, 3, prix_item)
                self.produits_table.setItem(row, 4, remise_item)
                self.produits_table.setItem(row, 5, total_item)
                
                # Ajouter le bouton de suppression
                delete_button = QPushButton("Supprimer")
                delete_button.setStyleSheet(self.table_button_style)
                delete_button.clicked.connect(lambda _, r=row: self.delete_product(r))
                self.produits_table.setCellWidget(row, 6, delete_button)
                
            # Charger les options
            options = get_options(dossier_id)
            
            # Afficher ou cacher le container des options selon s'il y en a ou non
            self.options_container.setVisible(bool(options))
            
            if options:
                self.options_table.setRowCount(len(options))
                for row, option in enumerate(options):
                    # Même logique que pour les produits
                    designation_item = QTableWidgetItem(option[2])
                    quantite_item = QTableWidgetItem(self.format_decimal(option[3]))
                    prix_item = QTableWidgetItem(self.format_decimal(option[4]))
                    remise_item = QTableWidgetItem(self.format_decimal(option[5]))
                    prix_unitaire = option[4]
                    remise = option[5]
                    prix_total = (option[3] * prix_unitaire) - remise
                    total_item = QTableWidgetItem(self.format_decimal(round(prix_total, 2)))
                    total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                    
                    self.options_table.setItem(row, 0, designation_item)
                    self.options_table.setItem(row, 1, quantite_item)
                    unite = option[6] if option[6] is not None else "aucune"
                    unite_combo = NoScrollComboBox()
                    unite_combo.addItems(["aucune", "m", "m²", "m³"])
                    unite_combo.setCurrentText(unite)
                    unite_combo.setFocusPolicy(Qt.NoFocus)
                    unite_combo.setStyleSheet(self.table_combo_style)
                    self.options_table.setCellWidget(row, 2, unite_combo)
                    self.options_table.setItem(row, 3, prix_item)
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
        self.adresse_facturation_custom_input.clear()
        self.acompte_demande_input.clear()
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
            "Acheminement materiel",
            "deplacement",
            "netoyage chantier",
            "mise en dechetterie payante"
        ]
        for produit in produits_obligatoires:
            row_position = self.produits_table.rowCount()
            self.produits_table.insertRow(row_position)
            self.produits_table.setItem(row_position, 0, QTableWidgetItem(produit))
            self.produits_table.setItem(row_position, 1, QTableWidgetItem("0"))
            unite_combo = NoScrollComboBox()
            unite_combo.addItems(["aucune", "m", "m²", "m³"])
            unite_combo.setFocusPolicy(Qt.NoFocus)
            unite_combo.setStyleSheet(self.table_combo_style)
            self.produits_table.setCellWidget(row_position, 2, unite_combo)
            self.produits_table.setItem(row_position, 3, QTableWidgetItem("0,0"))
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

    def add_product(self):
        row_position = self.produits_table.rowCount()
        self.produits_table.insertRow(row_position)
        self.produits_table.setItem(row_position, 0, QTableWidgetItem(""))
        self.produits_table.setItem(row_position, 1, QTableWidgetItem("0"))
        unite_combo = NoScrollComboBox()
        unite_combo.addItems(["aucune", "m", "m²", "m³"])
        unite_combo.setFocusPolicy(Qt.NoFocus)
        unite_combo.setStyleSheet(self.table_combo_style)
        self.produits_table.setCellWidget(row_position, 2, unite_combo)
        self.produits_table.setItem(row_position, 3, QTableWidgetItem("0,0"))
        self.produits_table.setItem(row_position, 4, QTableWidgetItem("0,0"))
        prix_total_item = QTableWidgetItem("0,0")
        prix_total_item.setFlags(prix_total_item.flags() & ~Qt.ItemIsEditable)
        self.produits_table.setItem(row_position, 5, prix_total_item)
        
        # Ajouter le bouton de suppression
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
        self.options_table.setItem(row_position, 1, QTableWidgetItem("0"))
        unite_combo = NoScrollComboBox()
        unite_combo.addItems(["aucune", "m", "m²", "m³"])
        unite_combo.setFocusPolicy(Qt.NoFocus)
        unite_combo.setStyleSheet(self.table_combo_style)
        self.options_table.setCellWidget(row_position, 2, unite_combo)
        self.options_table.setItem(row_position, 3, QTableWidgetItem("0,0"))
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
                result = subprocess.run([sys.executable, 'generate_devis.py', str(self.current_dossier_id)], check=True)
                if result.returncode == 0:
                    QMessageBox.information(self, "Devis", "Devis généré avec succès")
                else:
                    self.show_error_message("Erreur", "L'enregistrement du devis a été annulé")
            else:
                self.show_error_message("Erreur", "Aucun dossier sélectionné")
        except subprocess.CalledProcessError as e:
            if e.returncode != 1:
                self.show_error_message("Erreur", f"Une erreur s'est produite lors de la génération du devis : {e}")
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
                result = subprocess.run([sys.executable, 'generate_facture.py', str(self.current_dossier_id), invoice_type], check=True)
                if result.returncode == 0:
                    QMessageBox.information(self, "Facture", f"{invoice_type} générée avec succès")
            else:
                self.show_error_message("Erreur", "Aucun dossier sélectionné")
        except subprocess.CalledProcessError as e:
            if e.returncode != 1:
                self.show_error_message("Erreur", f"Une erreur s'est produite lors de la génération de la facture : {e}")
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite : {e}")

    def toggle_adresse_facturation(self, index):
        if (index == 1):  # "Autre" selected
            self.adresse_facturation_custom_input.setVisible(True)
        else:  # "Identique à l'adresse chantier" selected
            self.adresse_facturation_custom_input.setVisible(False)

    def enable_editing(self):
        self.is_editing = True
        self.numero_dossier_input.setReadOnly(False)
        self.adresse_chantier_input.setEnabled(True)  # Enable QComboBox in edit mode
        self.libelle_travaux_input.setReadOnly(False)
        self.adresse_facturation_input.setEnabled(True)
        self.acompte_demande_input.setReadOnly(False)
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
            unite_combo = self.produits_table.cellWidget(row, 2)
            if unite_combo:
                unite_combo.setEnabled(True)
                
        for row in range(self.options_table.rowCount()):
            delete_button = self.options_table.cellWidget(row, 6)
            if delete_button:
                delete_button.setEnabled(True)
            unite_combo = self.options_table.cellWidget(row, 2)
            if unite_combo:
                unite_combo.setEnabled(True)

    def disable_editing(self):
        self.is_editing = False
        self.numero_dossier_input.setReadOnly(True)
        self.adresse_chantier_input.setEnabled(False)  # Disable QComboBox in non-edit mode
        self.libelle_travaux_input.setReadOnly(True)
        self.adresse_facturation_input.setEnabled(False)
        self.acompte_demande_input.setReadOnly(True)
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
            unite_combo = self.produits_table.cellWidget(row, 2)
            if unite_combo:
                unite_combo.setEnabled(False)
                
        for row in range(self.options_table.rowCount()):
            delete_button = self.options_table.cellWidget(row, 6)
            if delete_button:
                delete_button.setEnabled(False)
            unite_combo = self.options_table.cellWidget(row, 2)
            if unite_combo:
                unite_combo.setEnabled(False)

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
        self.facture_view.load_factures()
        self.stacked_layout.setCurrentWidget(self.facture_view)
        self.dossiers_button.setStyleSheet(self.get_button_style(False))
        self.factures_button.setStyleSheet(self.get_button_style(True))
        self.devis_button.setStyleSheet(self.get_button_style(False))

    def show_devis(self):
        self.devis_view.load_devis()
        self.stacked_layout.setCurrentWidget(self.devis_view)
        self.dossiers_button.setStyleSheet(self.get_button_style(False))
        self.factures_button.setStyleSheet(self.get_button_style(False))
        self.devis_button.setStyleSheet(self.get_button_style(True))

    def show_dossiers(self):
        self.stacked_layout.setCurrentWidget(self.dossiers_splitter)
        self.dossiers_button.setStyleSheet(self.get_button_style(True))
        self.factures_button.setStyleSheet(self.get_button_style(False))
        self.devis_button.setStyleSheet(self.get_button_style(False))

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

def get_last_dossier_number():
    try:
        dossiers = get_dossiers()
        current_year = datetime.datetime.now().year
        year_dossiers = []
        
        for dossier in dossiers:
            numero = dossier[1]  # Récupère le numéro de dossier
            if '/' in numero:
                year, num = numero.split('/')
                if int(year) == current_year:
                    year_dossiers.append(int(num))
        
        if year_dossiers:
            return max(year_dossiers)
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
        
        # Set modern font
        font = QFont("Segoe UI", 12)
        app.setFont(font)

        # Apply stylesheet
        app.setStyleSheet(load_stylesheet())

        create_tables()
        window = MainWindow()
        window.show()

        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Critical Error", str(e))
        sys.exit(1)
