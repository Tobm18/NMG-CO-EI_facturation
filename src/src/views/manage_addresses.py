import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QMessageBox, QWidget, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from src.database.database import get_addresses, get_connection

class ManageAddressesDialog(QWidget):
    addresses_modified = pyqtSignal()  # Signal for address changes
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # Replace the main layout with a horizontal layout
        main_layout = QHBoxLayout(self)

        # Left side: search bar + addresses table
        left_layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Rechercher une adresse...")
        self.search_bar.textChanged.connect(self.filter_addresses)
        left_layout.addWidget(self.search_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Adresse"])
        
        # Disable direct cell editing
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Remove row numbers
        self.table.verticalHeader().setVisible(False)
        
        # Enable smooth pixel-by-pixel scrolling
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Style the header
        header = self.table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: rgb(55, 76, 96);
                color: white;
                padding: 8px;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # Additional table styling
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 0px;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)
        
        header.setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self.on_address_selected)
        left_layout.addWidget(self.table)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget)

        # Right side: form to edit, remove, or create addresses
        right_layout = QVBoxLayout()
        self.selected_address_input = QLineEdit()
        self.selected_address_input.setPlaceholderText("Adresse sélectionnée")
        right_layout.addWidget(self.selected_address_input)

        # Buttons for modifying, removing, or creating a new address
        buttons_layout = QHBoxLayout()
        self.modify_button = QPushButton("Modifier")
        self.modify_button.clicked.connect(self.modify_address)
        buttons_layout.addWidget(self.modify_button)

        self.delete_button = QPushButton("Supprimer")
        self.delete_button.clicked.connect(self.remove_selected_address)
        buttons_layout.addWidget(self.delete_button)

        self.new_button = QPushButton("Nouvelle")
        self.new_button.clicked.connect(self.add_new_address)
        buttons_layout.addWidget(self.new_button)

        right_layout.addLayout(buttons_layout)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget)

        # Load data
        self.load_addresses()

    def filter_addresses(self, query):
        # Simple search filtering by text
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            self.table.setRowHidden(row, query.lower() not in item.text().lower())

    def load_addresses(self):
        """Met à jour la table des adresses"""
        self.table.setRowCount(0)
        addresses = get_addresses()
        for address in addresses:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(address[1]))

    def on_address_selected(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        address_text = self.table.item(row, 0).text()
        self.selected_address_input.setText(address_text)

    def modify_address(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner une adresse à modifier.")
            return
            
        row = selected_items[0].row()
        old_address = self.table.item(row, 0).text()
        new_address = self.selected_address_input.text().strip()
        
        if not new_address:
            QMessageBox.warning(self, "Adresse vide", "Veuillez saisir une nouvelle adresse valide.")
            return
            
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Check if new address already exists (excluding current address)
            cursor.execute("SELECT address FROM addresses WHERE address = ? AND address != ?", 
                         (new_address, old_address))
            if cursor.fetchone():
                QMessageBox.warning(self, "Doublon", "Cette adresse existe déjà dans la base de données.")
                return
                
            cursor.execute("UPDATE addresses SET address = ? WHERE address = ?", 
                         (new_address, old_address))
            conn.commit()
            conn.close()
            self.load_addresses()
            self.selected_address_input.clear()
            self.addresses_modified.emit()  # Emit signal after successful modification
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Doublon", "Cette adresse existe déjà dans la base de données.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de modifier l'adresse: {e}")

    def add_new_address(self):
        """Create a new address from the text in the right panel."""
        address_text = self.selected_address_input.text().strip()
        if not address_text:
            QMessageBox.warning(self, "Adresse vide", "Veuillez saisir une adresse valide.")
            return
        try:
            # Check if address already exists
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT address FROM addresses WHERE address = ?", (address_text,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Doublon", "Cette adresse existe déjà dans la base de données.")
                return
            
            cursor.execute("INSERT INTO addresses (address) VALUES (?)", (address_text,))
            conn.commit()
            conn.close()
            self.load_addresses()
            self.selected_address_input.clear()
            self.addresses_modified.emit()  # Emit signal after successful addition
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Doublon", "Cette adresse existe déjà dans la base de données.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter l'adresse: {e}")

    def remove_selected_address(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Aucune sélection", "Veuillez sélectionner une adresse à supprimer.")
            return
        row = selected_items[0].row()
        address_text = self.table.item(row, 0).text()
        confirm = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer l'adresse suivante?\n\n{address_text}",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM addresses WHERE address = ?", (address_text,))
                conn.commit()
                conn.close()
                self.load_addresses()
                # Clear the selected address input field
                self.selected_address_input.clear()
                self.addresses_modified.emit()  # Emit signal after successful deletion
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer l'adresse: {e}")