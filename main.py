import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QFormLayout, QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QLabel, QStackedLayout, QHeaderView, QSplitter, QComboBox, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QFont, QIcon

from database import create_tables, add_dossier, get_dossiers, get_produits, add_produit, update_dossier, delete_produits

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NMG&CO Facturation")
        self.setGeometry(100, 100, 800, 600)

        # Définir l'icône de la fenêtre principale
        self.setWindowIcon(QIcon('NMG_CO.ico'))

        # Layout principal
        main_layout = QVBoxLayout()

        # Bandeau en haut de la page
        bandeau_layout = QHBoxLayout()
        self.bandeau_label = QLabel("Gestionnaire de facturation")
        self.bandeau_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.bandeau_button = QPushButton("Créer un nouveau dossier")
        self.bandeau_button.clicked.connect(self.new_dossier)
        bandeau_layout.addWidget(self.bandeau_label)
        bandeau_layout.addWidget(self.bandeau_button)

        # Layout pour le contenu principal
        content_splitter = QSplitter(Qt.Horizontal)

        # Liste scrollable des dossiers
        self.dossier_list = QListWidget()
        self.dossier_list.itemClicked.connect(self.load_dossier)
        content_splitter.addWidget(self.dossier_list)

        # StackedLayout pour basculer entre les vues
        self.stacked_layout = QStackedLayout()

        # Vue 1 : Sélection d'un dossier
        self.select_layout = QVBoxLayout()
        self.select_label = QLabel("Sélectionnez un Dossier")
        self.select_label.setAlignment(Qt.AlignCenter)
        self.new_dossier_button = QPushButton("Créer un nouveau dossier")
        self.new_dossier_button.clicked.connect(self.new_dossier)
        self.select_layout.addWidget(self.select_label)
        self.select_layout.addWidget(self.new_dossier_button)
        self.select_widget = QWidget()
        self.select_widget.setLayout(self.select_layout)

        # Vue 2 : Formulaire et tableau des produits
        self.form_layout = QFormLayout()
        self.numero_dossier_input = QLineEdit()
        self.adresse_chantier_input = QLineEdit()
        self.libelle_travaux_input = QLineEdit()
        self.adresse_facturation_input = QLineEdit()
        self.acompte_demande_input = QLineEdit()
        self.moyen_paiement_combo = QComboBox()
        self.moyen_paiement_combo.addItems(["Virement", "Espèces", "Chèque"])
        self.garantie_decennale_check = QCheckBox()
        self.description_input = QLineEdit()

        # Ajouter les champs au formulaire
        self.form_layout.addRow("Numéro dossier (YYYY/MM):", self.numero_dossier_input)
        self.form_layout.addRow("Adresse chantier:", self.adresse_chantier_input)
        self.form_layout.addRow("Libellé travaux:", self.libelle_travaux_input)
        self.form_layout.addRow("Adresse facturation:", self.adresse_facturation_input)
        self.form_layout.addRow("Acompte demandé (%):", self.acompte_demande_input)
        self.form_layout.addRow("Moyen de paiement:", self.moyen_paiement_combo)
        self.form_layout.addRow("Garantie décennale:", self.garantie_decennale_check)
        self.form_layout.addRow("Description:", self.description_input)

        self.save_button = QPushButton("Enregistrer")
        self.save_button.clicked.connect(self.save_dossier)
        self.form_layout.addWidget(self.save_button)

        self.produits_table = QTableWidget()
        self.produits_table.setColumnCount(7)
        self.produits_table.setHorizontalHeaderLabels(["Désignation", "Quantité", "Unité", "Prix Unitaire", "Remise", "Total", ""])
        self.produits_table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.produits_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.add_product_button = QPushButton("Ajouter un produit")
        self.add_product_button.clicked.connect(self.add_product)
        self.form_layout.addWidget(self.add_product_button)

        self.form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_layout.addLayout(self.form_layout)
        form_layout.addWidget(self.produits_table)

        # Ajouter les boutons "Générer un devis" et "Générer une facture"
        self.generate_quote_button = QPushButton("Générer un devis")
        self.generate_quote_button.clicked.connect(self.generate_quote)
        self.generate_invoice_button = QPushButton("Générer une facture")
        self.generate_invoice_button.clicked.connect(self.generate_invoice)
        form_layout.addWidget(self.generate_quote_button)
        form_layout.addWidget(self.generate_invoice_button)

        self.edit_button = QPushButton("Modifier le dossier")
        self.edit_button.clicked.connect(self.enable_editing)
        form_layout.addWidget(self.edit_button)

        self.form_widget.setLayout(form_layout)

        # Ajouter les deux vues au StackedLayout
        self.stacked_layout.addWidget(self.select_widget)
        self.stacked_layout.addWidget(self.form_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addLayout(self.stacked_layout)
        right_widget.setLayout(right_layout)
        content_splitter.addWidget(right_widget)

        content_splitter.setStretchFactor(0, 2)  
        content_splitter.setStretchFactor(1, 5)  

        # Ajouter le bandeau et le contenu principal au layout principal
        main_layout.addLayout(bandeau_layout)
        main_layout.addWidget(content_splitter)
        self.setLayout(main_layout)

        self.load_dossiers()
        self.show_select_message()

    def sanitize_input(self, text):
        return text.replace(',', '.')

    def format_decimal(self, value):
        return str(value).replace('.', ',')

    def load_dossiers(self):
        self.dossier_list.clear()
        dossiers = get_dossiers()
        for dossier in dossiers:
            self.dossier_list.addItem(f"{dossier[1]} - {dossier[3]}")

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)

    def save_dossier(self):
        try:
            numero_dossier = self.numero_dossier_input.text()
            adresse_chantier = self.adresse_chantier_input.text()
            libelle_travaux = self.libelle_travaux_input.text()
            adresse_facturation = self.adresse_facturation_input.text()
            acompte_demande = float(self.sanitize_input(self.acompte_demande_input.text()) or 0)
            moyen_paiement = self.moyen_paiement_combo.currentText()
            garantie_decennale = 1 if self.garantie_decennale_check.isChecked() else 0
            description = self.description_input.text()

            if not (numero_dossier and adresse_chantier):
                self.show_error_message("Erreur", "Veuillez remplir tous les champs obligatoires")
                return

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
                    description
                )
                if not self.save_produits(self.current_dossier_id):
                    return
            else:
                dossier_id = add_dossier(
                    numero_dossier,
                    adresse_chantier,
                    libelle_travaux,
                    adresse_facturation,
                    acompte_demande,
                    moyen_paiement,
                    garantie_decennale,
                    description
                )
                self.current_dossier_id = dossier_id
                if not self.save_produits(dossier_id):
                    return

            self.load_dossiers()
            self.load_dossier_by_id(self.current_dossier_id)
            self.disable_editing()  # Switch back to non-editable view
            QMessageBox.information(self, "Succès", "Dossier sauvegardé avec succès")
        except ValueError:
            self.show_error_message("Erreur de saisie", "Veuillez entrer des valeurs numériques valides pour les champs numériques.")
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite : {e}")

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
        except ValueError:
            self.show_error_message("Erreur de saisie", "Veuillez entrer des valeurs numériques valides pour les champs numériques.")
            return False
        except Exception as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors de la sauvegarde des produits : {e}")
            return False
        return True

    def load_dossier(self, item):
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
            self.adresse_chantier_input.setText(dossier[2])
            self.libelle_travaux_input.setText(dossier[3])
            self.adresse_facturation_input.setText(dossier[4])
            self.acompte_demande_input.setText(self.format_decimal(dossier[5]))
            self.moyen_paiement_combo.setCurrentText(dossier[6])
            self.garantie_decennale_check.setChecked(bool(int(dossier[7])))
            self.description_input.setText(dossier[8])
            
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
                prix_total = produit[3] * (prix_unitaire - remise)
                total_item = QTableWidgetItem(self.format_decimal(round(prix_total, 2)))
                total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
                self.produits_table.setItem(row, 0, designation_item)
                self.produits_table.setItem(row, 1, quantite_item)
                unite = produit[6] if produit[6] is not None else "aucune"
                unite_combo = NoScrollComboBox()
                unite_combo.addItems(["aucune", "m", "m²", "m3"])
                unite_combo.setCurrentText(unite)
                unite_combo.setFocusPolicy(Qt.NoFocus)
                self.produits_table.setCellWidget(row, 2, unite_combo)
                self.produits_table.setItem(row, 3, prix_item)
                self.produits_table.setItem(row, 4, remise_item)
                self.produits_table.setItem(row, 5, total_item)
                
                # Ajouter le bouton de suppression
                delete_button = QPushButton("Supprimer")
                delete_button.clicked.connect(lambda _, r=row: self.delete_product(r))
                self.produits_table.setCellWidget(row, 6, delete_button)
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

    def new_dossier(self):
        self.hide_select_message()
        # Effacer tous les champs
        self.numero_dossier_input.clear()
        self.adresse_chantier_input.clear()
        self.libelle_travaux_input.clear()
        self.adresse_facturation_input.clear()
        self.acompte_demande_input.clear()
        self.moyen_paiement_combo.setCurrentIndex(0)
        self.garantie_decennale_check.setChecked(False)
        self.description_input.clear()
        self.produits_table.setRowCount(0)
        
        if hasattr(self, 'current_dossier_id'):
            del self.current_dossier_id
    
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
            unite_combo.addItems(["aucune", "m", "m²", "m3"])
            unite_combo.setFocusPolicy(Qt.NoFocus)
            self.produits_table.setCellWidget(row_position, 2, unite_combo)
            self.produits_table.setItem(row_position, 3, QTableWidgetItem("0,0"))
            self.produits_table.setItem(row_position, 4, QTableWidgetItem("0,0"))
            prix_total_item = QTableWidgetItem("0,0")
            prix_total_item.setFlags(prix_total_item.flags() & ~Qt.ItemIsEditable)
            self.produits_table.setItem(row_position, 5, prix_total_item)
            
            # Ajouter le bouton de suppression
            delete_button = QPushButton("Supprimer")
            delete_button.clicked.connect(lambda _, r=row_position: self.delete_product(r))
            self.produits_table.setCellWidget(row_position, 6, delete_button)
        
        self.enable_editing()  # Switch to editable view

    def add_product(self):
        row_position = self.produits_table.rowCount()
        self.produits_table.insertRow(row_position)
        self.produits_table.setItem(row_position, 0, QTableWidgetItem(""))
        self.produits_table.setItem(row_position, 1, QTableWidgetItem("0"))
        unite_combo = NoScrollComboBox()
        unite_combo.addItems(["aucune", "m", "m²", "m3"])
        unite_combo.setFocusPolicy(Qt.NoFocus)
        self.produits_table.setCellWidget(row_position, 2, unite_combo)
        self.produits_table.setItem(row_position, 3, QTableWidgetItem("0,0"))
        self.produits_table.setItem(row_position, 4, QTableWidgetItem("0,0"))
        prix_total_item = QTableWidgetItem("0,0")
        prix_total_item.setFlags(prix_total_item.flags() & ~Qt.ItemIsEditable)
        self.produits_table.setItem(row_position, 5, prix_total_item)
        
        # Ajouter le bouton de suppression
        delete_button = QPushButton("Supprimer")
        delete_button.clicked.connect(lambda _, r=row_position: self.delete_product(r))
        self.produits_table.setCellWidget(row_position, 6, delete_button)

    def delete_product(self, row):
        self.produits_table.removeRow(row)
        # Update delete buttons to ensure correct row indices
        for row in range(self.produits_table.rowCount()):
            delete_button = QPushButton("Supprimer")
            delete_button.clicked.connect(lambda _, r=row: self.delete_product(r))
            self.produits_table.setCellWidget(row, 6, delete_button)

    def generate_quote(self):
        try:
            if hasattr(self, 'current_dossier_id'):
                result = subprocess.run([sys.executable, 'generate_devis.py', str(self.current_dossier_id)], check=True)
                if result.returncode == 0:
                    QMessageBox.information(self, "Devis", "Devis généré avec succès")
            else:
                self.show_error_message("Erreur", "Aucun dossier sélectionné")
        except subprocess.CalledProcessError as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors de la génération du devis : {e}")

    def generate_invoice(self):
        try:
            if hasattr(self, 'current_dossier_id'):
                result = subprocess.run([sys.executable, 'generate_facture.py', str(self.current_dossier_id)], check=True)
                if result.returncode == 0:
                    QMessageBox.information(self, "Facture", "Facture générée avec succès")
            else:
                self.show_error_message("Erreur", "Aucun dossier sélectionné")
        except subprocess.CalledProcessError as e:
            self.show_error_message("Erreur", f"Une erreur s'est produite lors de la génération de la facture : {e}")

    def show_select_message(self):
        self.stacked_layout.setCurrentWidget(self.select_widget)

    def hide_select_message(self):
        self.stacked_layout.setCurrentWidget(self.form_widget)

    def enable_editing(self):
        self.numero_dossier_input.setReadOnly(False)
        self.adresse_chantier_input.setReadOnly(False)
        self.libelle_travaux_input.setReadOnly(False)
        self.adresse_facturation_input.setReadOnly(False)
        self.acompte_demande_input.setReadOnly(False)
        self.moyen_paiement_combo.setEnabled(True)
        self.garantie_decennale_check.setEnabled(True)
        self.description_input.setReadOnly(False)
        self.produits_table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.save_button.setEnabled(True)
        self.add_product_button.setEnabled(True)
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

    def disable_editing(self):
        self.numero_dossier_input.setReadOnly(True)
        self.adresse_chantier_input.setReadOnly(True)
        self.libelle_travaux_input.setReadOnly(True)
        self.adresse_facturation_input.setReadOnly(True)
        self.acompte_demande_input.setReadOnly(True)
        self.moyen_paiement_combo.setEnabled(False)
        self.garantie_decennale_check.setEnabled(False)
        self.description_input.setReadOnly(True)
        self.produits_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.save_button.setEnabled(False)
        self.add_product_button.setEnabled(False)
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

if __name__ == "__main__":
    try:
        # Activer la mise à l'échelle DPI
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        
        # Optionnel : définir une police par défaut plus grande
        QFontDatabase.addApplicationFont(":/fonts/Roboto-Regular.ttf")
        app.setFont(QFont("Roboto", 12))

        create_tables()
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        error_message = f"Une erreur s'est produite : {e}"
        QMessageBox.critical(None, "Erreur Critique", error_message)
        sys.exit(1)