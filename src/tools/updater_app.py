from PyQt5.QtWidgets import QApplication, QMessageBox
import sys
import os
import subprocess
import requests
import ctypes
import time

def is_admin():
    """Vérifie si le programme a les droits administrateur"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relance le programme en tant qu'administrateur"""
    try:
        if getattr(sys, 'frozen', False):
            executable = sys.executable
            args = str(sys.argv[1])  
        else:           
            executable = sys.executable
            args = f'"{os.path.abspath(__file__)}" "{sys.argv[1]}"'

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas", 
            executable,
            args,
            os.path.dirname(executable),
            1
        )
        
        if result <= 32:
            return False

        time.sleep(2)            
        return True

    except Exception:
        return False

class UpdaterApp:
    def __init__(self, version_to_install):
        self.version = version_to_install
        self.download_url = "https://nmg.skietmontagnepegomas.com/download"
        
    def run(self):
        """Exécute la mise à jour"""
        if not is_admin():
            msg = QMessageBox()
            msg.setWindowTitle("Droits administrateur requis")
            msg.setText("La mise à jour nécessite les droits administrateur.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            if run_as_admin():
                QApplication.quit()
                sys.exit(0)
            else:
                QMessageBox.critical(None, "Erreur", "Impossible de lancer en mode administrateur.")
                return False

        msg = QMessageBox()
        msg.setWindowTitle("Mise à jour en cours")
        msg.setText("Téléchargement de la mise à jour...")
        msg.setStandardButtons(QMessageBox.NoButton)
        msg.show()
        QApplication.processEvents()

        update_file = self._download_update()
        if not update_file:
            msg.close()
            QMessageBox.critical(None, "Erreur", "Échec du téléchargement de la mise à jour.")
            return False
            
        msg.setText("Installation de la mise à jour...")
        QApplication.processEvents()
        
        if self._install_update(update_file):
            msg.close()
            QMessageBox.information(None, "Succès", "Mise à jour installée. Veuillez redémarer l'application.")
            return True
        
        msg.close()
        QMessageBox.critical(None, "Erreur", "Échec de l'installation de la mise à jour.")
        return False
        
    def _download_update(self):
        """Télécharge la nouvelle version"""
        try:
            url = f"{self.download_url}/{self.version}"
            
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                temp_dir = os.path.join(os.environ['TEMP'], 'NMGFacturation_update')
                update_file = os.path.join(temp_dir, f'NMGFacturation_v{self.version}.exe')
                
                os.makedirs(temp_dir, exist_ok=True)
                
                with open(update_file, 'wb') as f:
                    total_length = int(response.headers.get('content-length', 0))
                    
                    if total_length == 0:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                downloaded += len(chunk)
                                f.write(chunk)
                
                if os.path.exists(update_file):
                    size = os.path.getsize(update_file)
                    if size > 0:
                        return update_file
                    
                return None
                    
            return None
                
        except Exception:
            return None

    def _install_update(self, update_file):
        """Installe la nouvelle version"""
        try:
            # Correction du chemin d'installation
            if getattr(sys, 'frozen', False):
                app_path = os.path.dirname(sys.executable)
            else:
                # En développement, utiliser le chemin du projet
                app_path = os.path.join(os.environ['PROGRAMFILES'], 'NMGFacturation')
                
            script_path = os.path.join(os.environ['TEMP'], 'update.bat')
            
            with open(script_path, 'w') as f:
                f.write('@echo off\n')
                f.write('echo Demarrage de la mise a jour...\n')
                f.write('timeout /t 5 /nobreak\n')
                f.write('taskkill /F /IM NMGFacturation.exe >nul 2>&1\n')
                # Utiliser copy au lieu de xcopy pour éviter les problèmes de paramètres
                f.write(f'copy /Y "{update_file}" "{os.path.join(app_path, "NMGFacturation.exe")}" >nul\n')
                f.write('if errorlevel 1 (\n')
                f.write('  echo Erreur lors de la copie du fichier\n')
                f.write('  pause\n')
                f.write('  exit /b 1\n')
                f.write(')\n')
                f.write('echo Mise a jour terminee!\n')
                f.write('pause\n')
                f.write(f'start "" "{os.path.join(app_path, "NMGFacturation.exe")}"\n')
                f.write('del "%~f0"\n')

            # Lancement du script batch
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.Popen(
                ['cmd', '/c', script_path],
                shell=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return True
                
        except Exception:
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: NMGFacturationUpdater.exe <version>")
        sys.exit(1)
        
    app = QApplication(sys.argv)
    updater = UpdaterApp(sys.argv[1])
    success = updater.run()
    sys.exit(0 if success else 1)