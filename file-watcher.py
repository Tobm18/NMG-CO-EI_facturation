import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, script_name):
        self.script_name = script_name
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        self.process = subprocess.Popen([sys.executable, self.script_name])

    def on_modified(self, event):
        if event.src_path.endswith(".py") and any(event.src_path.endswith(script) for script in ["main.py", "liste_devis.py", "liste_facture.py"]):
            print(f"{event.src_path} modifié, relancement de l'application...")
            self.start_process()

def watch_files(script_name):
    event_handler = ReloadHandler(script_name)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)  # Surveille le répertoire actuel
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        event_handler.process.terminate()
        event_handler.process.wait()
    observer.join()

if __name__ == "__main__":
    script_name = "main.py"  # Nom du fichier à surveiller
    watch_files(script_name)