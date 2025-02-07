import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView, QMessageBox, QLineEdit, QHBoxLayout, QComboBox
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt
from src.database.database import get_dossiers, get_produits  # Correction de l'import
import subprocess

class ListeDevis(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liste des Devis")
        self.setGeometry(100, 100, 1280, 720)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Création d'un layout horizontal pour la recherche et le filtre
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 10)  # Add bottom margin to the layout
        search_layout.setSpacing(10)  # Add spacing between widgets
        
        # Ajout du champ de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 1px solid #005980;
            }
        """)
        
        # Ajout du filtre de statut
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "Signé", "Non signé"])
        self.status_filter.currentTextChanged.connect(self.filter_table)
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                min-width: 120px;
                font-size: 14px;
                min-height: 20px;
            }
        """)
        
        search_layout.addWidget(self.search_input, stretch=1)  # Give search input more space
        search_layout.addWidget(self.status_filter)
        self.main_layout.addLayout(search_layout)

        # Tableau des devis
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Changed from 5 to 6
        self.table.setHorizontalHeaderLabels(["Numéro Dossier", "Adresse Chantier", "Adresse Facturation", "Libellé Travaux", "Statut", "Télécharger"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                background-color: #f9f9f9;
                gridline-color: transparent;
                alternate-background-color: #e0e0e0;  
            }
            QTableWidget::item {
                margin: 10px;
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: rgb(55, 76, 96);
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)

        self.main_layout.addWidget(self.table)

        self.load_devis()

    def load_devis(self):
        dossiers = get_dossiers()
        self.table.setRowCount(len(dossiers))
        for row, dossier in enumerate(dossiers):
            columns = [
                (1, "numero_dossier"),
                (2, "adresse_chantier"),
                (4, "adresse_facturation"),  # Index corrigé de 7 à 4
                (3, "libelle_travaux")
            ]
            
            for col, (index, _) in enumerate(columns):
                item = QTableWidgetItem(str(dossier[index]))
                item.setFlags(Qt.ItemIsEnabled)
                if row % 2 == 0:
                    item.setBackground(QColor("#f9f9f9"))
                else:
                    item.setBackground(QColor("#e0e0e0"))
                self.table.setItem(row, col, item)

            # Statut de signature
            devis_signe = dossier[8]
            item_signe = QTableWidgetItem("Signé" if devis_signe == 1 else "Non signé")
            item_signe.setForeground(QBrush(QColor("green") if devis_signe == 1 else QColor("red")))
            item_signe.setFlags(Qt.ItemIsEnabled)
            item_signe.setTextAlignment(Qt.AlignCenter)
            if row % 2 == 0:
                item_signe.setBackground(QColor("#f9f9f9"))
            else:
                item_signe.setBackground(QColor("#e0e0e0"))
            self.table.setItem(row, 4, item_signe)  # Index 4 pour le statut

            # Bouton de téléchargement
            download_button = QPushButton("Télécharger le devis")
            download_button.clicked.connect(lambda _, d_id=dossier[0]: self.generate_devis(d_id))
            self.table.setCellWidget(row, 5, download_button)  # Index 5 pour le bouton

    def filter_table(self):
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentText()
        
        for row in range(self.table.rowCount()):
            show_row = False
            match_text = False
            match_status = False
            
            # Vérification du texte de recherche
            for col in range(self.table.columnCount() - 1):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match_text = True
                    break
            
            # Vérification du statut
            status_item = self.table.item(row, 3)
            if status_filter == "Tous":
                match_status = True
            elif status_filter == "Signé" and status_item.text() == "Signé":
                match_status = True
            elif status_filter == "Non signé" and status_item.text() == "Non signé":
                match_status = True
                
            show_row = match_text and match_status
            self.table.setRowHidden(row, not show_row)

    def calculate_total_devis(self, dossier_id):
        try:
            produits = get_produits(dossier_id)
            total = 0
            for produit in produits:
                prix_unitaire = float(produit[4])  # prix unitaire à l'index 4
                remise = float(produit[5])  # remise à l'index 5
                quantite = produit[3]  # quantité (TEXT) à l'index 3
                
                # Calcul du total selon le type de quantité
                if quantite and quantite not in ["Forfait", "Ensemble"]:
                    try:
                        quantite_num = float(str(quantite).replace(',', '.'))
                        total += (quantite_num * prix_unitaire) - remise
                    except (ValueError, TypeError):
                        total += prix_unitaire - remise
                else:
                    total += prix_unitaire - remise
                    
            return total
        except Exception as e:
            print(f"Erreur dans calculate_total_devis: {e}")
            return 0

    def generate_devis(self, dossier_id):
        try:
            from src.utils.generate_devis import generate_devis
            if generate_devis(dossier_id):
                QMessageBox.information(self, "Devis", "Devis téléchargé avec succès")
            else:
                # Ne rien faire si l'utilisateur a annulé
                pass
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ListeDevis()
    window.show()
    sys.exit(app.exec_())
