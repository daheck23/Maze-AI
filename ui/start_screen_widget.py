# ui/start_screen_widget.py
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal

class StartScreenWidget(QWidget):
    start_game_requested = pyqtSignal(str) # Sendet den Dateipfad der ausgewählten Map
    show_highscores_requested = pyqtSignal(str) # Sendet den Map-Namen für Highscores
    generate_new_map_requested = pyqtSignal()
    exit_game_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.map_folder = "assets/maps" # Pfad zu den Map-Dateien

        self.setup_ui()
        self.load_maps()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Titel
        title_label = QLabel("Maze Game - Hauptmenü")
        title_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #4CAF50;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(40)

        # Maps Liste
        map_list_label = QLabel("Verfügbare Labyrinthe:")
        map_list_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        main_layout.addWidget(map_list_label)

        self.map_list_widget = QListWidget()
        self.map_list_widget.setFixedSize(300, 200)
        self.map_list_widget.setStyleSheet(
            "QListWidget { background-color: #333; color: white; border: 1px solid #666; }"
            "QListWidget::item { padding: 5px; }"
            "QListWidget::item:selected { background-color: #555; }"
        )
        self.map_list_widget.currentItemChanged.connect(self.on_map_selection_changed)
        main_layout.addWidget(self.map_list_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacing(20)

        # Buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Start Labyrinth Button
        self.start_button = QPushButton("Labyrinth starten")
        self.start_button.setFixedSize(200, 50)
        self.start_button.setStyleSheet("background-color: #007BFF; color: white; font-size: 18px; border-radius: 10px;")
        self.start_button.clicked.connect(self.on_start_button_clicked)
        self.start_button.setEnabled(False) # Initial deaktiviert
        buttons_layout.addWidget(self.start_button)
        
        # Highscores Button
        self.highscores_button = QPushButton("Highscores anzeigen")
        self.highscores_button.setFixedSize(200, 50)
        self.highscores_button.setStyleSheet("background-color: #28A745; color: white; font-size: 18px; border-radius: 10px;")
        self.highscores_button.clicked.connect(self.on_highscores_button_clicked)
        self.highscores_button.setEnabled(False) # Initial deaktiviert
        buttons_layout.addWidget(self.highscores_button)

        # Neue Map generieren Button (Platzhalter)
        self.generate_map_button = QPushButton("Neue Map generieren")
        self.generate_map_button.setFixedSize(200, 50)
        self.generate_map_button.setStyleSheet("background-color: #FFC107; color: black; font-size: 18px; border-radius: 10px;")
        self.generate_map_button.clicked.connect(self.generate_new_map_requested.emit)
        buttons_layout.addWidget(self.generate_map_button)

        # Beenden Button
        self.exit_button = QPushButton("Beenden")
        self.exit_button.setFixedSize(200, 50)
        self.exit_button.setStyleSheet("background-color: #DC3545; color: white; font-size: 18px; border-radius: 10px;")
        self.exit_button.clicked.connect(self.exit_game_requested.emit)
        buttons_layout.addWidget(self.exit_button)

        main_layout.addLayout(buttons_layout)
        main_layout.addStretch(1)

        self.setStyleSheet("background-color: #222; color: white;")

    def load_maps(self):
        self.map_list_widget.clear()
        if not os.path.exists(self.map_folder):
            self.map_list_widget.addItem("Fehler: Map-Ordner nicht gefunden.")
            self.start_button.setEnabled(False)
            self.highscores_button.setEnabled(False)
            return

        map_files = [f for f in os.listdir(self.map_folder) if f.endswith(".map")]
        
        if not map_files:
            self.map_list_widget.addItem("Keine .map-Dateien gefunden im Ordner: " + self.map_folder)
            self.start_button.setEnabled(False)
            self.highscores_button.setEnabled(False)
            return

        for map_file in sorted(map_files):
            self.map_list_widget.addItem(map_file)
        
        if self.map_list_widget.count() > 0:
            self.map_list_widget.setCurrentRow(0) # Wählt die erste Map aus

    def on_map_selection_changed(self, current, previous):
        # Aktiviere Buttons, wenn eine Map ausgewählt ist (current ist nicht None)
        self.start_button.setEnabled(current is not None)
        self.highscores_button.setEnabled(current is not None)

    def on_start_button_clicked(self):
        selected_item = self.map_list_widget.currentItem()
        if selected_item:
            map_filename = selected_item.text()
            map_filepath = os.path.join(self.map_folder, map_filename)
            self.start_game_requested.emit(map_filepath)

    def on_highscores_button_clicked(self):
        selected_item = self.map_list_widget.currentItem()
        if selected_item:
            map_filename = selected_item.text()
            map_name = os.path.splitext(map_filename)[0]
            self.show_highscores_requested.emit(map_name)