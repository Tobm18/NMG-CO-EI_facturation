import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt
from database import get_dossiers, get_produits

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
            }
            QTableWidget::item {
                margin: 10px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)
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
                    item.setBackground(QColor("#f2f2f2"))
                self.table.setItem(row, col, item)
            facture_payee = dossier[10]
            item_payee = QTableWidgetItem("Payé" if facture_payee else "Non payé")
            item_payee.setForeground(QBrush(QColor("green") if facture_payee else QColor("red")))
            item_payee.setFlags(Qt.ItemIsEnabled)
            if row % 2 == 0:
                item_payee.setBackground(QColor("#f9f9f9"))
            else:
                item_payee.setBackground(QColor("#f2f2f2"))
            self.table.setItem(row, 3, item_payee)
            download_button = QPushButton("Télécharger la facture")
            download_button.clicked.connect(lambda _, d_id=dossier[0]: self.download_facture(d_id))
            self.table.setCellWidget(row, 4, download_button)

    def calculate_total_facture(self, dossier_id):
        produits = get_produits(dossier_id)
        total = sum((produit[3] * produit[4]) - produit[5] for produit in produits)
        return total

    def download_facture(self, dossier_id):
        # Placeholder for downloading logic
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ListeFacture()
    window.show()
    sys.exit(app.exec_())
