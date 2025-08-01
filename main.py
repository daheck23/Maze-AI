import sys
from PyQt6.QtWidgets import QApplication
# Importiere deine MainWindow-Klasse aus dem ui-Ordner
from ui.main_window import MazeGame # Stelle sicher, dass der Klassenname MazeGame ist

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Erstelle eine Instanz deines Hauptfensters
    game = MazeGame()
    game.show()
    sys.exit(app.exec())