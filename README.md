# NMG-CO-EI Facturation

Application de facturation développée pour NMG&CO-EI.

## Installation rapide
- 📥 [Télécharger l'installateur](https://github.com/Tobm18/NMG-CO-EI_facturation/raw/main/NMGFacturationInstaller.exe)
- 📥 [Télécharger le désinstallateur](https://github.com/Tobm18/NMG-CO-EI_facturation/raw/main/NMGFacturationUninstaller.exe)

## Structure du projet

```
src/ 
├── builders/                        # Scripts de compilation 
│   ├── build_app.py                 # Compilation de l'application 
│   ├── build_installer.py           # Compilation de l'installateur 
│   ├── build_uninstaller.py         # Compilation du désinstallateur 
│   └── build_updater.py             # Compilation de l'utilitaire de mise à jours 
├── src/
│   ├── assets/
│   │   ├── Img/                     # Images et icônes 
│   │   └── style.qss                # Feuilles de style Qt 
│   ├── database/
│   │   ├── database.py              # Classes et méthodes BDD 
│   │   └── databaseinit.py          # Initialisation BDD 
│   ├── utils/
│   │   ├── generate_devis.py        # Génération PDF devis 
│   │   └── generate_facture.py      # Génération PDF factures 
│   ├── views/
│   │   ├── liste_devis.py           # Interface gestion devis 
│   │   ├── liste_facture.py         # Interface gestion factures 
│   │   └── manage_addresses.py      # Interface gestion adresses 
│   ├── version.py                   # Version de l'application 
│   └── main.py                      # Point d'entrée de l'application 
├── tools/
│   ├── installer_app.py             # Script de l'installateur 
│   ├── uninstaller_app.py           # Script du désinstallateur 
│   └── updater_app.py               # Script de l'utilitaire de mise à jours 
└── requirements.txt                 # Dépendances Python 
```

## Modification du projet

Si vous devez apporter des modifications au code source, vous aurrez ensuite besoin de le recompiler, suivez ces étapes pour recompiler l'application :

### Prérequis

[Installer Python 3.13.2 pour Windows](https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe)

```bash
# Se placer dans le répertoire src/
cd .\src\

# Installation des dépendances Python
pip install -r .\requirements.txt
```

### Compilation

Pour compiler les différents composants, placez-vous dans le dossier src et utilisez les commandes suivantes :

```bash
# Compiler l'application principale
python -m builders.build_app

# Compiler l'installateur
python -m builders.build_installer

# Compiler le désinstallateur
python -m builders.build_uninstaller

# Compiler l'updater
python -m builders.build_updater
```

Les fichiers compilés se trouveront dans le dossier dist/.

**Important: Avant toute compilation, pensez à mettre à jour le numéro de version dans le fichier version.py.**

## Note

Les modifications du code source nécessitent une recompilation complète de l'application.  
Lorsque l'app est installée avec l'installateur exécutable, celle-ci se trouve dans *C:\Program Files\NMGFacturation*  
Le fichier de base de données se trouve à l'emplacement *C:\Users\%USER%\AppData\Local\NMGFacturation\data*
