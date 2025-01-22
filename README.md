# NMG-CO-EI Facturation

Application de facturation développée pour NMG&CO-EI.

## Installation rapide
- 📥 [Télécharger l'installateur](https://github.com/Tobm18/NMG-CO-EI_facturation/raw/main/NMGFacturationInstaller.exe)
- 📥 [Télécharger le désinstallateur](https://github.com/Tobm18/NMG-CO-EI_facturation/raw/main/NMGFacturationUninstaller.exe)

## Structure du projet

```
src/ 
├──src/
│  ├── assets/                         
│  │   ├── Img/                      # Images et icônes 
│  │   └── style.qss                 # Feuilles de style Qt 
│  ├── database/                        
│  │   ├── database.py               # Classes et méthodes BDD 
│  │   └── databaseinit.py           # Initialisation BDD 
│  ├── utils/                            
│  │   ├── generate_devis.py         # Génération PDF devis 
│  │   └── generate_facture.py       # Génération PDF factures 
│  ├── views/                           
│  │   ├── liste_devis.py            # Interface gestion devis 
│  │   └── liste_facture.py          # Interface gestion factures 
│  └── main.py                       # Point d'entrée de l'application 
├── NMGFacturation.spec              # Configuration compilation de l'app 
├── NMGFacturationInstaller.spec     # Configuration compilation de l'installateur
├── NMGFacturationUninstaller.spec   # Configuration compilation du désinstallateur 
├── create_uninstaller.py            # Script de création du désinstallateur 
├── installer.py                     # Script de création de l'installateur 
├── setup.py                         # Script d'installation 
├── uninstaller.py                   # Script de désinstallation 
└── requirements.txt                 # Dépendances Python
```

## Modification du projet

Si vous devez apporter des modifications au code source, vous aurrez ensuite besoin de le recompiler, suivez ces étapes pour recompiler l'application :

### Prérequis

```bash
# Installation des dépendances Python
pip install -r src/requirements.txt

# Installer PyInstaller pour la compilation
pip install pyinstaller
```

### Compilation

Pour recompiler l'application et les installateurs:

1. Compiler l'application principale:

```bash
pyinstaller src/NMGFacturation.spec
```

2. Compiler l'installateur:

```bash
pyinstaller src/NMGFacturationInstaller.spec
```

3. Compiler le désinstallateur:

```bash
pyinstaller src/NMGFacturationUninstaller.spec
```

Les fichiers compilés se trouveront dans le dossier dist/.

## Note

Les modifications du code source nécessitent une recompilation complète de l'application et des installateurs.