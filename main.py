# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
# Importiere die MainWindow-Klasse aus ui/main_window.py
from ui.main_window import MainWindow 

def create_project_directories():
    """
    Erstellt alle notwendigen Projektverzeichnisse, falls sie nicht existieren.
    """
    print("DEBUG: Überprüfe und erstelle Projektverzeichnisse...")
    
    # Hauptverzeichnisse
    base_dirs = ["assets", "ai", "game", "ui", "trained-models"]
    for d in base_dirs:
        path = os.path.join(os.getcwd(), d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Verzeichnis erstellt: {path}")

    # Unterverzeichnisse in 'assets'
    assets_sub_dirs = ["images", "maps", "sounds", "scores"]
    for sd in assets_sub_dirs:
        path = os.path.join(os.getcwd(), "assets", sd)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Verzeichnis erstellt: {path}")
    print("DEBUG: Verzeichnisprüfung abgeschlossen.")

def main():
    """
    Hauptfunktion zum Starten der Anwendung.
    """
    # Stelle sicher, dass die Ordnerstruktur korrekt ist
    create_project_directories()
    
    # Erstelle die PyQt-Anwendung
    app = QApplication(sys.argv)
    
    # Instanziiere das Hauptfenster der Anwendung
    # Diese MainWindow-Klasse befindet sich in ui/main_window.py
    window = MainWindow() 
    
    # Zeige das Hauptfenster an
    window.show()
    
    # Starte die Ereignisschleife der Anwendung
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
