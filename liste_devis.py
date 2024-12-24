import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QAbstractItemView, QMessageBox
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt  # Add this import
from database import get_dossiers, get_produits
import subprocess

class ListeDevis(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liste des Devis")
        self.setGeometry(100, 100, 1280, 720)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Tableau des devis
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Numéro Dossier", "Adresse Chantier", "Libellé Travaux", "Status", "Télécharger"])
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
            for col in range(3):
                item = QTableWidgetItem(dossier[col + 1])
                item.setFlags(Qt.ItemIsEnabled)
                if row % 2 == 0:
                    item.setBackground(QColor("#f9f9f9"))
                else:
                    item.setBackground(QColor("#e0e0e0"))
                self.table.setItem(row, col, item)
            devis_signe = dossier[9]
            item_signe = QTableWidgetItem("Signé" if devis_signe else "Non signé")
            item_signe.setForeground(QBrush(QColor("green") if devis_signe else QColor("red")))
            item_signe.setFlags(Qt.ItemIsEnabled)
            item_signe.setTextAlignment(Qt.AlignCenter)  # Center align the text
            if row % 2 == 0:
                item_signe.setBackground(QColor("#f9f9f9"))
            else:
                item_signe.setBackground(QColor("#e0e0e0"))
            self.table.setItem(row, 3, item_signe)
            download_button = QPushButton("Télécharger le devis")
            download_button.clicked.connect(lambda _, d_id=dossier[0]: self.generate_devis(d_id))
            self.table.setCellWidget(row, 4, download_button)

    def calculate_total_devis(self, dossier_id):
        produits = get_produits(dossier_id)
        total = sum((produit[3] * produit[4]) - produit[5] for produit in produits)
        return total

    def generate_devis(self, dossier_id):
        try:
            result = subprocess.run([sys.executable, 'generate_devis.py', str(dossier_id)], check=True)
            if result.returncode == 0:
                QMessageBox.information(self, "Devis", "Devis téléchargé avec succès")
        except subprocess.CalledProcessError as e:
            if e.returncode != 1:
                QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors du téléchargement du devis : {e}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ListeDevis()
    window.show()
    sys.exit(app.exec_())
