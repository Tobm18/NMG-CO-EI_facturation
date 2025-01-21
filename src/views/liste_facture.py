import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView, QMessageBox, QDialog, QLabel, QDialogButtonBox, QComboBox
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
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Numéro Dossier", "Adresse Chantier", "Libellé Travaux", "Status", "Télécharger"])
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
        self.table.setRowCount(len(dossiers))
        for row, dossier in enumerate(dossiers):
            for col in range(3):
                item = QTableWidgetItem(dossier[col + 1])
                item.setFlags(Qt.ItemIsEnabled)
                if row % 2 == 0:
                    item.setBackground(QColor("#f9f9f9"))
                else:
                    item.setBackground(QColor("#e0e0e0"))
                self.table.setItem(row, col, item)
            facture_payee = dossier[10]
            item_payee = QTableWidgetItem("Payé" if facture_payee else "Non payé")
            item_payee.setForeground(QBrush(QColor("green") if facture_payee else QColor("red")))
            item_payee.setFlags(Qt.ItemIsEnabled)
            item_payee.setTextAlignment(Qt.AlignCenter)  # Center align the text
            if row % 2 == 0:
                item_payee.setBackground(QColor("#f9f9f9"))
            else:
                item_payee.setBackground(QColor("#e0e0e0"))
            self.table.setItem(row, 3, item_payee)
            download_button = QPushButton("Télécharger la facture")
            download_button.clicked.connect(lambda _, d_id=dossier[0]: self.show_invoice_type_dialog(d_id))
            self.table.setCellWidget(row, 4, download_button)

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
            result = subprocess.run([sys.executable, 'generate_facture.py', str(dossier_id), invoice_type], check=True)
            if result.returncode == 0:
                QMessageBox.information(self, "Facture", f"{invoice_type} téléchargée avec succès")
        except subprocess.CalledProcessError as e:
            if e.returncode != 1:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors du téléchargement de la facture : {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def calculate_total_facture(self, dossier_id):
        produits = get_produits(dossier_id)
        total = sum((produit[3] * produit[4]) - produit[5] for produit in produits)
        return total

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ListeFacture()
    window.show()
    sys.exit(app.exec_())
