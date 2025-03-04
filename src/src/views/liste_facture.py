import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView, QMessageBox, QDialog, QLabel, QDialogButtonBox, QComboBox, QLineEdit, QHBoxLayout  # Add this import
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt
from src.database.database import get_dossiers, get_produits  # Correction de l'import

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, e):
        e.ignore()

class ListeFacture(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liste des Factures")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        
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
        self.status_filter.addItems(["Tous", "Payé", "Non payé"])
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
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)  # Changed from 5 to 6
        self.table.setHorizontalHeaderLabels(["Numéro Dossier", "Adresse Chantier", "Adresse Facturation", "Libellé Travaux", "Statut", "Télécharger"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
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
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.load_factures()

    def load_factures(self):
        dossiers = get_dossiers()
        # Filtrer les dossiers où facture_generated == 1
        dossiers_avec_facture = [d for d in dossiers if d[11] == 1]  # index 11 pour facture_generated
    
        self.table.setRowCount(len(dossiers_avec_facture))
        for row, dossier in enumerate(dossiers_avec_facture):
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

            # Statut de paiement
            facture_payee = dossier[9]
            item_payee = QTableWidgetItem("Payé" if facture_payee == 1 else "Non payé")
            item_payee.setForeground(QBrush(QColor("green") if facture_payee == 1 else QColor("red")))
            item_payee.setFlags(Qt.ItemIsEnabled)
            item_payee.setTextAlignment(Qt.AlignCenter)
            if row % 2 == 0:
                item_payee.setBackground(QColor("#f9f9f9"))
            else:
                item_payee.setBackground(QColor("#e0e0e0"))
            self.table.setItem(row, 4, item_payee)  # Index 4 pour le statut

            # Bouton de téléchargement
            download_button = QPushButton("Télécharger la facture")
            download_button.clicked.connect(lambda _, d_id=dossier[0]: self.show_invoice_type_dialog(d_id))
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
            elif status_filter == "Payé" and status_item.text() == "Payé":
                match_status = True
            elif status_filter == "Non payé" and status_item.text() == "Non payé":
                match_status = True
                
            show_row = match_text and match_status
            self.table.setRowHidden(row, not show_row)

    def show_invoice_type_dialog(self, dossier_id):
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
        buttons.accepted.connect(lambda: self.generate_facture(dialog, dossier_id))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec_()

    def generate_facture(self, dialog, dossier_id):
        invoice_type = self.invoice_type_combo.currentText()
        dialog.accept()
        try:
            from src.utils.generate_facture import generate_facture
            result = generate_facture(dossier_id, invoice_type)
            if result:
                QMessageBox.information(self, "Facture", f"{invoice_type} téléchargée avec succès")
            else:
                # Ne rien faire si l'utilisateur a annulé
                pass
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def calculate_total_facture(self, dossier_id):
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
            print(f"Erreur dans calculate_total_facture: {e}")
            return 0

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ListeFacture()
    window.show()
    sys.exit(app.exec_())
