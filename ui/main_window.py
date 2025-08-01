# ui/main_window.py
import sys
import os 
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QStackedWidget, QMessageBox, QPushButton, QInputDialog
)
from PyQt6.QtCore import QTimer, QDateTime, Qt

from ui.game_board_widget import GameBoardWidget
from ui.start_screen_widget import StartScreenWidget
from game.maze_logic import MazeLogic
from game.maze_generator import MazeGenerator

class MainWindow(QMainWindow):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.setWindowTitle("Maze Game")
        self.setGeometry(100, 100, 800, 600)

        self.maze_logic = MazeLogic()
        self.maze_generator = MazeGenerator() 
        self.current_loaded_map_path = ""

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # 1. Startbildschirm erstellen und zum Stack hinzufügen
        self.start_screen = StartScreenWidget()
        self.stacked_widget.addWidget(self.start_screen) # Index 0

        # Signale vom Startbildschirm verbinden
        self.start_screen.start_game_requested.connect(self.start_game)
        self.start_screen.show_highscores_requested.connect(self.show_highscores_screen)
        self.start_screen.generate_new_map_requested.connect(self.generate_new_maze) 
        self.start_screen.exit_game_requested.connect(self.close)

        # 2. Spielbrett erstellen und zum Stack hinzufügen (noch nicht sichtbar)
        self.game_board_widget = GameBoardWidget(self.maze_logic)
        self.stacked_widget.addWidget(self.game_board_widget) # Index 1

        # Info-Bereich (wird nur sichtbar sein, wenn GameBoardWidget angezeigt wird)
        self.info_layout_widget = QWidget()
        info_layout = QHBoxLayout(self.info_layout_widget)
        
        self.return_to_menu_button = QPushButton("Menü")
        self.return_to_menu_button.setStyleSheet("background-color: #6C757D; color: white; font-size: 14px; border-radius: 5px;")
        self.return_to_menu_button.clicked.connect(self.show_start_screen)
        info_layout.addWidget(self.return_to_menu_button)

        self.restart_game_button = QPushButton("Neues Spiel")
        self.restart_game_button.setStyleSheet("background-color: #17A2B8; color: white; font-size: 14px; border-radius: 5px;")
        self.restart_game_button.clicked.connect(self.restart_current_game)
        info_layout.addWidget(self.restart_game_button)

        info_layout.addSpacing(20)
        
        self.keys_label = QLabel("Schlüssel: 0")
        self.keys_label.setStyleSheet("font-size: 16px; font-weight: bold; color: yellow;")
        info_layout.addWidget(self.keys_label)

        self.ducks_label = QLabel("Enten: 0")
        self.ducks_label.setStyleSheet("font-size: 16px; font-weight: bold; color: orange;")
        info_layout.addWidget(self.ducks_label)
        
        info_layout.addStretch(1) 

        self.time_label = QLabel("Zeit: 00:00")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        info_layout.addWidget(self.time_label)

        main_layout.insertWidget(0, self.info_layout_widget)
        self.info_layout_widget.hide()

        # Initialisiere Timer und verbinde Signale der MazeLogic
        self.start_time = QDateTime.currentDateTime() 
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_time_display)
        
        self.maze_logic.keys_changed.connect(self.update_keys_display)
        self.maze_logic.ducks_changed.connect(self.update_ducks_display)
        self.maze_logic.game_won.connect(self.handle_game_won)
        
        # Zeige beim Start den Startbildschirm
        self.show_start_screen()

    def show_start_screen(self):
        self.stacked_widget.setCurrentWidget(self.start_screen)
        self.info_layout_widget.hide()
        self.game_timer.stop()
        self.maze_logic.game_over = False 
        self.game_board_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.start_screen.setFocus()
        self.start_screen.load_maps()

    def start_game(self, map_filepath):
        self.current_loaded_map_path = map_filepath
        self._load_and_start_game(map_filepath)

    def restart_current_game(self):
        if self.current_loaded_map_path:
            self._load_and_start_game(self.current_loaded_map_path)
        else:
            QMessageBox.warning(self, "Fehler", "Kein Labyrinth geladen, um neu zu starten.")
            self.show_start_screen()

    def _load_and_start_game(self, map_filepath):
        if self.maze_logic.load_maze_from_file(map_filepath):
            self.stacked_widget.setCurrentWidget(self.game_board_widget)
            self.info_layout_widget.show()

            self.start_time = QDateTime.currentDateTime()
            self.maze_logic.game_over = False 
            self.update_keys_display(self.maze_logic.get_collected_keys_count())
            self.update_ducks_display(self.maze_logic.get_collected_ducks_count())
            self.update_time_display()
            self.game_timer.start(1000)

            self.game_board_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus) 
            self.game_board_widget.setFocus()
            self.game_board_widget.update()
        else:
            QMessageBox.critical(self, "Fehler", f"Konnte Labyrinth '{map_filepath}' nicht laden.")
            self.show_start_screen()

    def show_highscores_screen(self, map_name):
        QMessageBox.information(self, "Highscores", f"Highscores für {map_name} werden hier angezeigt (noch nicht implementiert).")

    def generate_new_maze(self):
        width, ok = QInputDialog.getInt(self, "Labyrinth Generieren", "Breite (ungerade Zahl empfohlen):", 
                                        41, 11, 101, 2)
        if not ok: return

        height, ok = QInputDialog.getInt(self, "Labyrinth Generieren", "Höhe (ungerade Zahl empfohlen):", 
                                         21, 11, 61, 2)
        if not ok: return
        
        num_keys, ok = QInputDialog.getInt(self, "Labyrinth Generieren", "Anzahl Schlüssel:", 
                                           3, 0, 10, 1)
        if not ok: return

        num_ducks, ok = QInputDialog.getInt(self, "Labyrinth Generieren", "Anzahl Enten:", 
                                            2, 0, 10, 1)
        if not ok: return

        try:
            generated_maze_raw = self.maze_generator.generate_maze(width, height)
            final_maze_data = self.maze_generator.add_elements_to_maze(generated_maze_raw, num_keys, num_ducks)

            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
            filename = f"generated_maze_{timestamp}.map"
            
            filepath = self.maze_generator.save_maze_to_file(final_maze_data, filename)

            QMessageBox.information(self, "Labyrinth Generiert", f"Neues Labyrinth erfolgreich gespeichert als:\n{filename}")
            
            self.start_screen.load_maps()
            self.start_screen.map_list_widget.setCurrentRow(self.start_screen.map_list_widget.count() - 1) 

        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Generieren", f"Ein Fehler ist aufgetreten: {e}\nPrüfe die Konsolenausgabe für Details.")
            print(f"Error generating maze: {e}") 

    def update_keys_display(self, count):
        self.keys_label.setText(f"Schlüssel: {count} / {self.maze_logic.total_keys}")

    def update_ducks_display(self, count):
        self.ducks_label.setText(f"Enten: {count} / {self.maze_logic.total_rewards}")

    def update_time_display(self):
        if not self.maze_logic.is_game_over(): 
            elapsed_seconds = self.start_time.secsTo(QDateTime.currentDateTime())
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            self.time_label.setText(f"Zeit: {minutes:02}:{seconds:02}")
        else:
            self.game_timer.stop() 

    def handle_game_won(self):
        self.game_timer.stop()
        self.maze_logic.game_over = True
        QMessageBox.information(self, "Spiel gewonnen!", f"Glückwunsch, du hast das Labyrinth in {self.time_label.text().replace('Zeit: ', '')} geschafft!")
        QTimer.singleShot(500, self.show_start_screen)
    
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Spiel beenden', 'Bist du sicher, dass du das Spiel beenden möchtest?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.app_instance.quit()
            event.accept()
        else:
            event.ignore()