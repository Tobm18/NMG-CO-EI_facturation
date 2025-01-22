import os
import sys
import shutil
import winshell
import ctypes
from win32api import MessageBox
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def get_app_paths():
    app_data = os.path.join(os.getenv('LOCALAPPDATA'), 'NMGFacturation')
    data_dir = os.path.join(app_data, 'data')
    install_dir = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'NMGFacturation')
    desktop = str(Path.home() / "Desktop")
    
    return {
        'app_data': app_data,
        'data_dir': data_dir,
        'install_dir': install_dir, 
        'desktop': desktop
    }

def remove_shortcut(desktop):
    shortcut_path = os.path.join(desktop, "NMGFacturation.lnk")
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        print(f"Raccourci supprimé: {shortcut_path}")

def uninstall():
    if not is_admin():
        print("Requesting administrator privileges...")
        run_as_admin()
        sys.exit()

    try:
        paths = get_app_paths()
        
        # Demander à l'utilisateur s'il veut conserver les données
        keep_data = MessageBox(None, 
            "Voulez-vous conserver les données de l'application ? \n\n" +
            "(Cliquez 'Oui' pour conserver les données, 'Non' pour tout supprimer)", 
            "Désinstallation", 
            4) == 6  # 6 = Yes, 7 = No
        
        # Supprimer le raccourci
        remove_shortcut(paths['desktop'])
        
        # Supprimer le dossier d'installation
        if os.path.exists(paths['install_dir']):
            shutil.rmtree(paths['install_dir'])
            print(f"Application supprimée de {paths['install_dir']}")
        
        # Supprimer les données si l'utilisateur a choisi de ne pas les conserver
        if not keep_data and os.path.exists(paths['app_data']):
            shutil.rmtree(paths['app_data'])
            print(f"Données supprimées de {paths['app_data']}")
        
        MessageBox(None, 
            "Désinstallation terminée avec succès!" +
            ("\n\nLes données ont été conservées dans %LOCALAPPDATA%\\NMGFacturation" if keep_data else ""), 
            "Désinstallation")
        
    except Exception as e:
        MessageBox(None, f"Erreur lors de la désinstallation: {e}", "Erreur")
        sys.exit(1)

if __name__ == '__main__':
    uninstall()