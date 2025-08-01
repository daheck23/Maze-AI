import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt # Importiere Qt für Ausrichtung etc.

# Importiere dein neues GameBoardWidget
from ui.game_board_widget import GameBoardWidget
# Importiere deine MazeLogic Klasse
from game.maze_logic import MazeLogic

class MazeGame(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dave's Labyrinth Adventure (PyQt Edition)") # Titel des Fensters
        self.setGeometry(100, 100, 1000, 750) # (x, y, Breite, Höhe) des Fensters, etwas größer

        # Erstelle eine Instanz deiner MazeLogic
        self.maze_logic = MazeLogic() 

        self.init_ui()

    def init_ui(self):
        # Haupt-Layout für das gesamte Fenster
        main_layout = QHBoxLayout() # Wir verwenden ein horizontales Layout für Spielbereich und Seitenleiste

        # --- Linker Bereich: Das Labyrinth selbst ---
        # Gib die MazeLogic-Instanz an das GameBoardWidget weiter
        # HIER WURDE DIE KORREKTUR VORGENOMMEN: maze_logic_instance wird übergeben
        self.game_board = GameBoardWidget(self.maze_logic) 
        main_layout.addWidget(self.game_board, 3) # Nimmt 3/4 des Platzes ein

        # --- Rechter Bereich: Seitenleiste für Infos und Buttons ---
        sidebar_layout = QVBoxLayout() # Vertikales Layout für die Seitenleiste
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Elemente oben ausrichten

        # Beispiel-Labels für Informationen
        self.score_label = QLabel("Punkte: 0")
        self.score_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.keys_label = QLabel("Schlüssel: 0")
        self.keys_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self.time_label = QLabel("Zeit: 00:00")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")


        sidebar_layout.addWidget(self.score_label)
        sidebar_layout.addWidget(self.keys_label)
        sidebar_layout.addWidget(self.time_label)

        sidebar_layout.addStretch(1) # Fügt dehnbaren Leerraum hinzu, um die Elemente nach oben zu drücken

        # Beispiel-Buttons
        button_style = "QPushButton { font-size: 14px; padding: 8px; border: 1px solid #aaa; border-radius: 5px; background-color: #f0f0f0; }" \
                       "QPushButton:hover { background-color: #e0e0e0; }" \
                       "QPushButton:pressed { background-color: #d0d0d0; }"

        self.start_game_button = QPushButton("Labyrinth starten")
        self.start_game_button.setStyleSheet(button_style)
        self.train_ai_button = QPushButton("KI trainieren")
        self.train_ai_button.setStyleSheet(button_style)
        self.show_ai_path_button = QPushButton("KI Pfad zeigen")
        self.show_ai_path_button.setStyleSheet(button_style)
        self.learning_demo_button = QPushButton("KI Lern-Demo starten") # Neuer Button für deine Idee
        self.learning_demo_button.setStyleSheet(button_style)
        self.back_to_menu_button = QPushButton("Zurück zum Menü")
        self.back_to_menu_button.setStyleSheet(button_style)
        self.exit_button = QPushButton("Beenden")
        self.exit_button.setStyleSheet(button_style + "QPushButton { background-color: #ffcccc; } QPushButton:hover { background-color: #ffaaaa; }") # Roter für Exit

        sidebar_layout.addWidget(self.start_game_button)
        sidebar_layout.addWidget(self.train_ai_button)
        sidebar_layout.addWidget(self.show_ai_path_button)
        sidebar_layout.addWidget(self.learning_demo_button)
        sidebar_layout.addWidget(self.back_to_menu_button)
        sidebar_layout.addWidget(self.exit_button)

        # Verbinden des Exit-Buttons mit der Schließfunktion
        self.exit_button.clicked.connect(self.close)

        main_layout.addLayout(sidebar_layout, 1) # Setze die Seitenleiste ins Haupt-Layout
        self.setLayout(main_layout) # Setze das Haupt-Layout für das Fenster