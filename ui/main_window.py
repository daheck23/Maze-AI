# ui/main_window.py
# Dies ist das Hauptfenster der Anwendung, das die UI-Elemente verwaltet.

import os
import sys
import random 
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel,
    QInputDialog, QMessageBox, QComboBox, QStackedWidget,
    QDialog, QLineEdit, QSpinBox, QDialogButtonBox, QFormLayout,
    QTextBrowser, QTableWidget, QTableWidgetItem, QHeaderView 
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime 

# Importiere die Logik- und Generator-Klassen
from game.maze_logic import MazeLogic
from ui.game_board_widget import GameBoardWidget
from ui.maze_generator import MazeGenerator
from ai.agent import Agent # Import des KI-Agenten

# --- Benutzerdefinierter Dialog für die Labyrinthgenerierung ---
class MazeGenerationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Labyrinth generieren")
        self.setModal(True) # Macht den Dialog modal (blockiert das Hauptfenster)

        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("z.B. mein_neues_labyrinth")

        self.width_input = QSpinBox()
        self.width_input.setRange(10, 100) # Mindestgröße 10, Maximal 100
        self.width_input.setValue(15) # Standardwert

        self.height_input = QSpinBox()
        self.height_input.setRange(10, 100) # Mindestgröße 10, Maximal 100
        self.height_input.setValue(15) # Standardwert

        # OK- und Abbrechen-Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept) # Verbindet OK mit accept()
        self.buttons.rejected.connect(self.reject) # Verbindt Cancel mit reject()

        # Layout für den Dialog
        form_layout = QFormLayout()
        form_layout.addRow("Dateiname (ohne .map):", self.filename_input)
        form_layout.addRow("Breite (min 10):", self.width_input)
        form_layout.addRow("Höhe (min 10):", self.height_input)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.buttons)
        self.setLayout(main_layout)

    def get_inputs(self):
        """Gibt die vom Benutzer eingegebenen Werte zurück."""
        return self.filename_input.text(), self.width_input.value(), self.height_input.value()

# --- Hauptfenster der Anwendung ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maze AI Game")
        self.setGeometry(100, 100, 800, 600) # Standardfenstergröße

        # Instanziiere die Logik- und Generator-Klassen
        self.maze_logic = MazeLogic()
        self.maze_generator = MazeGenerator()

        # Das Spielbrett-Widget (wird die Labyrinth-Grafik anzeigen)
        self.game_board_widget = GameBoardWidget(self.maze_logic)

        # Timer für die Spielzeit (für manuelle Spiele)
        self.timer = QTimer(self)
        self.game_time_seconds = 0

        # KI-Agent und KI-Timer (für AI-Spiele/Training)
        self.agent = Agent(self.maze_logic) # Agent-Instanz erstellen
        self.agent.load_model() # Modell beim Start automatisch laden
        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self.ai_make_move)
        self.ai_move_interval = 20 # Standard-Bewegungsintervall in ms (schneller für KI-Training)
        self.current_episode = 0 # Zähler für KI-Episoden

        # Variablen zum Speichern des letzten KI-Zugs und dessen Ergebnis
        self.last_ai_move_vector = None
        self.last_ai_move_resulted_in_wall_hit = False

        # Initialisiere die Benutzeroberfläche (Startbildschirm und Spielbildschirm)
        self.init_ui()
        
        # Zeige den Startbildschirm beim Programmstart
        self.show_start_screen()

    def init_ui(self):
        """
        Initialisiert die Haupt-Benutzeroberfläche mit einem StackedWidget
        zum Wechseln zwischen verschiedenen Ansichten (Startbildschirm, Spielbildschirm, Highscores).
        """
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Erstelle die Hauptansichten und füge sie dem StackedWidget hinzu
        self.create_start_screen()
        self.create_game_screen()
        self.create_highscores_screen()

        # Verbinde Signale von der Spiellogik mit den UI-Updates
        self.maze_logic.maze_updated.connect(self.game_board_widget.update)
        self.maze_logic.keys_changed.connect(self.update_key_display)
        self.maze_logic.ducks_changed.connect(self.update_reward_display)
        self.maze_logic.game_won.connect(self.handle_game_won)
        self.maze_logic.game_lost.connect(self.handle_game_lost)
        self.maze_logic.message_display_requested.connect(self.display_temp_message) # Verbindung für Nachrichten
        self.timer.timeout.connect(self.update_timer)


    def create_start_screen(self):
        """
        Erstellt das Widget und Layout für den Startbildschirm des Spiels.
        """
        self.start_screen_widget = QWidget()
        start_layout = QVBoxLayout(self.start_screen_widget)
        start_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Zentriert den Inhalt vertikal

        # Titel des Spiels
        title_label = QLabel("Willkommen im Maze AI Game!")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Zentriert den Text
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 20px;")
        start_layout.addWidget(title_label)

        # Bereich für die Map-Auswahl (ComboBox und Start-Button)
        map_selection_layout = QHBoxLayout()
        self.map_selector = QComboBox()
        self.map_selector.setPlaceholderText("Wähle ein Labyrinth...")
        self.map_selector.setMinimumWidth(250)
        map_selection_layout.addWidget(QLabel("Verfügbare Labyrinthe:"))
        map_selection_layout.addWidget(self.map_selector)

        self.start_game_button = QPushButton("Labyrinth starten (Manuell)")
        self.start_game_button.clicked.connect(self.start_selected_maze_game) 
        map_selection_layout.addWidget(self.start_game_button)

        # Button für AI-Spiel
        self.start_ai_game_button = QPushButton("Labyrinth starten (KI)")
        self.start_ai_game_button.clicked.connect(self.start_selected_maze_game_ai)
        map_selection_layout.addWidget(self.start_ai_game_button)

        start_layout.addLayout(map_selection_layout)

        # Weitere Buttons auf dem Startbildschirm
        self.generate_maze_button_start = QPushButton("Neues Labyrinth generieren")
        self.generate_maze_button_start.clicked.connect(self.generate_new_maze)
        start_layout.addWidget(self.generate_maze_button_start)

        self.highscores_button = QPushButton("Highscores anzeigen")
        self.highscores_button.clicked.connect(self.show_highscores_screen)
        self.highscores_button.setEnabled(True)
        start_layout.addWidget(self.highscores_button)

        self.exit_button_start = QPushButton("Beenden")
        self.exit_button_start.clicked.connect(self.close)
        start_layout.addWidget(self.exit_button_start)
        
        # Füge diesen Startbildschirm zum StackedWidget hinzu
        self.stacked_widget.addWidget(self.start_screen_widget)

    def create_game_screen(self):
        """
        Erstellt das Widget und Layout für den eigentlichen Spielbildschirm.
        Das Layout wird in drei Bereiche unterteilt:
        1. Obere Leiste für Statistiken (QHBoxLayout)
        2. Mittlerer Bereich für das Labyrinth (Game Board Widget)
        3. Rechter Bereich für Buttons (QVBoxLayout)
        """
        self.game_screen_widget = QWidget()
        
        # Hauptlayout für den Spielbildschirm (teilt den Bildschirm horizontal)
        main_game_layout = QHBoxLayout(self.game_screen_widget)

        # Linker Bereich: Statistiken oben, Labyrinth unten (vertikal gestapelt)
        left_section_layout = QVBoxLayout()
        
        # Obere Leiste für Spielstatistiken (Schlüssel, Enten, Zeit, Punkte)
        stats_layout = QHBoxLayout()
        self.key_count_label = QLabel("Schlüssel: 0/0")
        self.reward_count_label = QLabel("Enten: 0/0")
        self.timer_label = QLabel("Zeit: 00:00")
        self.score_label = QLabel("Punkte: 0")
        self.ai_info_label = QLabel("KI-Episode: N/A | Epsilon: N/A") # Für KI-Infos
        self.status_message_label = QLabel("") # Label für temporäre Nachrichten
        self.status_message_label.setStyleSheet("color: red; font-weight: bold;") # Optional: Stil für Nachrichten

        stats_layout.addWidget(self.key_count_label)
        stats_layout.addWidget(self.reward_count_label)
        stats_layout.addWidget(self.timer_label)
        stats_layout.addWidget(self.score_label)
        stats_layout.addWidget(self.ai_info_label) # Füge KI-Info-Label hinzu
        stats_layout.addStretch(1) # Schiebt Labels nach links
        stats_layout.addWidget(self.status_message_label) # Füge Status-Nachrichten-Label hinzu

        left_section_layout.addLayout(stats_layout)
        
        # Das GameBoardWidget nimmt den restlichen vertikalen Platz ein
        left_section_layout.addWidget(self.game_board_widget, 1) # Stretch-Faktor 1

        main_game_layout.addLayout(left_section_layout, 1) # Linker Bereich nimmt den meisten Platz ein

        # Rechter Bereich: Buttons vertikal gestapelt
        right_buttons_layout = QVBoxLayout()
        right_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Buttons oben ausrichten
        
        self.back_to_menu_button = QPushButton("Zurück zum Menü")
        self.back_to_menu_button.clicked.connect(self.show_start_screen)
        right_buttons_layout.addWidget(self.back_to_menu_button)

        self.restart_ai_episode_button = QPushButton("Neuer Durchgang (KI)") # Restart-Button
        self.restart_ai_episode_button.clicked.connect(self.start_new_ai_episode)
        self.restart_ai_episode_button.hide() # Zunächst versteckt
        right_buttons_layout.addWidget(self.restart_ai_episode_button)

        self.learn_ai_button = QPushButton("AI lernen (noch nicht implementiert)")
        self.learn_ai_button.setEnabled(False) # Deaktiviert
        right_buttons_layout.addWidget(self.learn_ai_button)

        self.exit_game_button = QPushButton("Beenden")
        self.exit_game_button.clicked.connect(self.close) # Direkter Exit aus dem Spiel
        right_buttons_layout.addWidget(self.exit_game_button)

        right_buttons_layout.addStretch(1) # Schiebt Buttons nach oben

        main_game_layout.addLayout(right_buttons_layout) # Rechter Bereich für Buttons

        self.stacked_widget.addWidget(self.game_screen_widget)

    def create_highscores_screen(self):
        """
        Erstellt das Widget und Layout für den Highscore-Bildschirm.
        """
        self.highscores_screen_widget = QWidget()
        hs_layout = QVBoxLayout(self.highscores_screen_widget)
        hs_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Highscores")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 20px;")
        hs_layout.addWidget(title_label)

        # Tabelle für die Highscores
        self.highscores_table = QTableWidget()
        self.highscores_table.setColumnCount(5) # Datum, Map, Punkte, Zeit (min:sek), Zeitbonus
        self.highscores_table.setHorizontalHeaderLabels(["Datum", "Map", "Punkte", "Zeit", "Bonus"])
        self.highscores_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Spalten füllen den Platz
        self.highscores_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Nicht editierbar
        hs_layout.addWidget(self.highscores_table)

        self.highscores_map_label = QLabel("Highscores für: Keine Map ausgewählt")
        self.highscores_map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hs_layout.addWidget(self.highscores_map_label)

        back_button = QPushButton("Zurück zum Menü")
        back_button.clicked.connect(self.show_start_screen)
        hs_layout.addWidget(back_button)

        self.stacked_widget.addWidget(self.highscores_screen_widget)


    def show_start_screen(self):
        """
        Wechselt zur Ansicht des Startbildschirms.
        """
        print("Zeige Startbildschirm an.")
        self.stacked_widget.setCurrentWidget(self.start_screen_widget)
        self.update_map_list() 
        self.timer.stop() # Stoppt den Timer, falls im Spiel gewesen
        self.ai_timer.stop() # Stoppt den AI-Timer
        self.maze_logic.game_over = True # Setzt den Spielzustand zurück
        self.maze_logic.is_ai_controlled = False # AI-Steuerung deaktivieren
        self.maze_logic.maze = [] # Leert das Labyrinth, damit das Spielfeld 'sauber' ist
        self.maze_logic.maze_updated.emit() # Signalisiert dem GameBoardWidget, sich zu aktualisieren (leeres Feld)
        
        # Verstecke KI-spezifische Buttons
        self.restart_ai_episode_button.hide()
        self.ai_info_label.setText("KI-Episode: N/A | Epsilon: N/A") # KI-Info zurücksetzen
        self.status_message_label.setText("") # Nachrichten-Label leeren


    def show_game_screen(self):
        """
        Wechselt zur Ansicht des Spielbildschirms.
        """
        print("Zeige Spielbildschirm an.")
        self.stacked_widget.setCurrentWidget(self.game_screen_widget)
        # Fokus wird in start_new_game oder start_ai_game gesetzt
        # self.game_board_widget.setFocus() 

    def show_highscores_screen(self):
        """
        Wechselt zur Ansicht des Highscore-Bildschirms und lädt die Highscores.
        """
        print("Zeige Highscores an.")
        self.stacked_widget.setCurrentWidget(self.highscores_screen_widget)
        self.load_and_display_highscores()


    def update_map_list(self):
        """
        Aktualisiert die Liste der verfügbaren Labyrinthe in der ComboBox.
        """
        print("update_map_list wird ausgeführt.")
        maps_dir = "assets/maps"
        self.map_selector.clear()
        self.map_selector.addItem("Wähle ein Labyrinth...") # Placeholder

        # Sicherstellen, dass der Ordner existiert, bevor wir ihn lesen
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir) # Erstellt den Ordner, falls er nicht existiert
            print(f"Verzeichnis '{maps_dir}' erstellt.")

        map_files = [f for f in os.listdir(maps_dir) if f.endswith('.map')]
        
        if not map_files:
            print("Keine .map-Dateien im Ordner gefunden.")
            self.map_selector.addItem("Keine Labyrinthe gefunden")
            self.map_selector.setEnabled(False)
            self.start_game_button.setEnabled(False)
            self.start_ai_game_button.setEnabled(False)
        else:
            print(f"Gefundene Maps: {map_files}")
            self.map_selector.addItems(sorted(map_files))
            self.map_selector.setEnabled(True)
            self.start_game_button.setEnabled(True)
            self.start_ai_game_button.setEnabled(True)

    def start_selected_maze_game(self):
        """
        Startet ein ausgewähltes Labyrinth für manuelle Steuerung.
        """
        if self.map_selector.currentIndex() == 0: # Placeholder ausgewählt
            QMessageBox.warning(self, "Auswahl erforderlich", "Bitte wählen Sie ein Labyrinth aus der Liste, um das Spiel zu starten.")
            return

        selected_file = self.map_selector.currentText()
        filepath = os.path.join("assets", "maps", selected_file)
        
        self.maze_logic.is_ai_controlled = False # Wichtig: AI-Steuerung deaktivieren
        print(f"DEBUG: Manuelles Spiel gestartet. is_ai_controlled = {self.maze_logic.is_ai_controlled}")
        self.load_maze_and_start_game(filepath)

    def start_selected_maze_game_ai(self):
        """
        Startet ein ausgewähltes Labyrinth für AI-Steuerung.
        """
        if self.map_selector.currentIndex() == 0: # Placeholder ausgewählt
            QMessageBox.warning(self, "Auswahl erforderlich", "Bitte wählen Sie ein Labyrinth aus der Liste, um das Spiel mit der KI zu starten.")
            return

        selected_file = self.map_selector.currentText()
        filepath = os.path.join("assets", "maps", selected_file)
        
        self.maze_logic.is_ai_controlled = True # Wichtig: AI-Steuerung aktivieren
        print(f"DEBUG: KI-Spiel gestartet. is_ai_controlled = {self.maze_logic.is_ai_controlled}")
        self.load_maze_and_start_game(filepath)


    def load_maze_and_start_game(self, filepath):
        """
        Lädt eine Map und startet das Spiel.
        """
        print(f"DEBUG: load_maze_and_start_game: Beginn. is_ai_controlled = {self.maze_logic.is_ai_controlled}")
        if self.maze_logic.load_maze_from_file(filepath):
            print(f"Labyrinth '{filepath}' geladen. Spiel startet.")
            self.show_game_screen() # Wechselt zur Spielansicht
            self.start_new_game() # Startet die Spiel-Logik (Timer etc.)
            
            # Zeige/Verstecke KI-spezifische Buttons
            if self.maze_logic.is_ai_controlled:
                self.ai_timer.start(self.ai_move_interval)
                self.game_board_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Deaktiviere Fokus für manuelle Eingabe
                self.restart_ai_episode_button.show()
                self.current_episode = 1 # Starte mit Episode 1
                self.update_ai_info_display()
                print("DEBUG: Fokus-Policy auf NoFocus gesetzt (KI-Steuerung). KI-Buttons sichtbar.")
            else:
                self.ai_timer.stop() # Sicherstellen, dass der AI-Timer gestoppt ist
                self.game_board_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Aktiviere Fokus für manuelle Eingabe
                self.game_board_widget.setFocus() # Setze Fokus für manuelle Steuerung
                self.activateWindow() # Fenster aktivieren
                self.raise_()         # Fenster in den Vordergrund bringen
                self.restart_ai_episode_button.hide()
                self.ai_info_label.setText("KI-Episode: N/A | Epsilon: N/A") # KI-Info zurücksetzen
                print("DEBUG: Fokus-Policy auf StrongFocus gesetzt und Fokus gesetzt (manuelle Steuerung). KI-Buttons versteckt.")

        else:
            QMessageBox.critical(self, "Fehler", f"Konnte Labyrinth '{filepath}' nicht laden. Möglicherweise beschädigt oder ungültig.")
            self.show_start_screen()


    def generate_new_maze(self):
        """
        Öffnet einen benutzerdefinierten Dialog zur Eingabe von Dateinamen, Breite und Höhe
        und generiert dann das Labyrinth.
        """
        dialog = MazeGenerationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            filename, width, height = dialog.get_inputs()
            
            if not filename:
                filename = f"generated_maze_{width}x{height}_{random.randint(1000, 9999)}"
                QMessageBox.information(self, "Info", f"Kein Name eingegeben, speichere als: {filename}.map")

            final_maze_path = os.path.join("assets", "maps", f"{filename}.map")
            
            self.generate_new_maze_with_size_and_load(width, height, save_path=final_maze_path)
        else:
            print("Labyrinthgenerierung abgebrochen.")


    def generate_new_maze_with_size_and_load(self, width, height, save_path=None):
        """
        Generiert ein Labyrinth mit gegebener Größe, speichert es und kehrt dann zum Startbildschirm zurück.
        """
        print(f"Generiere Labyrinth {width}x{height}...")
        generated_maze_data = self.maze_generator.generate_maze(width, height)
        print(f"MazeGenerator.generate_maze returned. Shape: {len(generated_maze_data)}x{len(generated_maze_data[0]) if generated_maze_data and len(generated_maze_data) > 0 else 'N/A'}")

        final_maze_data = self.maze_generator.add_elements_to_maze(generated_maze_data)
        print(f"MazeGenerator.add_elements_to_maze returned. Shape: {len(final_maze_data)}x{len(final_maze_data[0]) if final_maze_data and len(final_maze_data) > 0 else 'N/A'}")
        
        try:
            with open(save_path, 'w') as f:
                for r_idx, row in enumerate(final_maze_data):
                    row_str = "".join(row)
                    f.write(row_str + "\n")
            print(f"Erfolgreich Labyrinth nach {save_path} geschrieben.")
            self.update_map_list()
            
            self.show_start_screen() 

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern des Labyrinths: {e}")
            self.show_start_screen()
            return
        
    def load_maze_from_dialog(self):
        """
        Platzhalterfunktion zum Laden eines Labyrinths über einen Dateidialog.
        Wird durch die ComboBox-Auswahl ersetzt.
        """
        QMessageBox.information(self, "Labyrinth laden", "Bitte nutzen Sie die Dropdown-Liste 'Verfügbare Labyrinthe' und den Button 'Labyrinth starten'.")


    def start_new_game(self):
        """
        Setzt den Spielzustand zurück und startet den Timer neu, wenn ein neues Spiel beginnt.
        """
        print("Starte neues Spiel.")
        self.game_time_seconds = 0
        self.timer.start(1000)
        self.update_timer()
        self.update_key_display()
        self.update_reward_display()
        self.score_label.setText(f"Punkte: {self.maze_logic.get_current_score()}")
        self.maze_logic.maze_updated.emit()


    def ai_make_move(self):
        """
        Lässt den KI-Agenten einen Zug machen und führt einen Lernschritt aus.
        Wird vom ai_timer aufgerufen.
        """
        if self.maze_logic.is_game_over():
            self.ai_timer.stop()
            print("DEBUG: AI Timer gestoppt, Spiel vorbei.")
            # Modell automatisch speichern, wenn der Durchgang beendet ist
            self.agent.save_model() 
            return

        if not self.maze_logic.is_ai_controlled:
            print("DEBUG: AI-Timer läuft, aber Spiel ist nicht KI-gesteuert. Stoppe AI-Timer.")
            self.ai_timer.stop()
            return

        # 1. Aktuellen Zustand erfassen
        state = self.maze_logic.get_state_representation()
        
        # 2. Aktion wählen (epsilon-greedy), unter Berücksichtigung des letzten Zuges
        chosen_move_vector = self.agent.choose_action(
            state,
            self.last_ai_move_resulted_in_wall_hit,
            self.last_ai_move_vector
        )

        # 3. Aktion ausführen und Belohnung/neuen Zustand erhalten
        reward, done = self.maze_logic.move_player(chosen_move_vector[0], chosen_move_vector[1])
        
        # Speichere den letzten Zug und ob er zu einem Wandtreffer führte
        self.last_ai_move_vector = chosen_move_vector
        self.last_ai_move_resulted_in_wall_hit = (reward == self.maze_logic.REWARD_WALL_HIT)

        # 4. Neuen Zustand erfassen
        next_state = self.maze_logic.get_state_representation()

        # 5. Agent lernen lassen
        loss = self.agent.learn(state, self.agent.get_action_index(chosen_move_vector[0], chosen_move_vector[1]), reward, next_state, done)
        self.update_ai_info_display() # Aktualisiere KI-Infos im UI

        if done:
            self.ai_timer.stop()
            print(f"DEBUG: KI-Durchgang {self.current_episode} beendet.")
            # Modell automatisch speichern, wenn der Durchgang beendet ist
            self.agent.save_model() 
            # Hier keine QMessageBox, da die handle_game_won/lost dies bereits tun
            # und das Fenster offen bleiben soll.


    def start_new_ai_episode(self):
        """
        Startet einen neuen KI-Trainingsdurchgang auf der aktuellen Map.
        """
        print("DEBUG: Starte neuen KI-Trainingsdurchgang.")
        self.current_episode += 1
        self.maze_logic.reset_game_for_ai_training() # Setzt das Labyrinth zurück
        self.game_time_seconds = 0 # Setzt die Zeit zurück
        self.timer.start(1000) # Startet den Spielzeit-Timer
        self.ai_timer.start(self.ai_move_interval) # Startet den KI-Bewegungs-Timer
        self.update_ai_info_display() # Aktualisiere KI-Infos
        self.update_key_display()
        self.update_reward_display()
        self.score_label.setText(f"Punkte: {self.maze_logic.get_current_score()}")
        self.maze_logic.maze_updated.emit()

        # Setze die letzten Zug-Informationen für den neuen Durchgang zurück
        self.last_ai_move_vector = None
        self.last_ai_move_resulted_in_wall_hit = False


    def update_key_display(self):
        """Aktualisiert die Anzeige der gesammelten Schlüssel im UI."""
        collected = self.maze_logic.get_collected_keys_count()
        total = self.maze_logic.total_keys
        self.key_count_label.setText(f"Schlüssel: {collected}/{total}")

    def update_reward_display(self):
        """Aktualisiert die Anzeige der gesammelten Enten/Belohnungen und den Punktestand im UI."""
        collected = self.maze_logic.get_collected_ducks_count()
        total = self.maze_logic.get_total_rewards_count()
        self.reward_count_label.setText(f"Enten: {collected}/{total}")
        self.score_label.setText(f"Punkte: {self.maze_logic.get_current_score()}")

    def update_timer(self):
        """Aktualisiert die Zeitanzeige im UI jede Sekunde."""
        self.game_time_seconds += 1
        minutes = self.game_time_seconds // 60
        seconds = self.game_time_seconds % 60
        self.timer_label.setText(f"Zeit: {minutes:02d}:{seconds:02d}")

    def update_ai_info_display(self):
        """Aktualisiert die Anzeige der KI-Informationen im UI."""
        self.ai_info_label.setText(f"KI-Episode: {self.current_episode} | Epsilon: {self.agent.epsilon:.4f}")

    def display_temp_message(self, message):
        """
        Zeigt eine temporäre Nachricht im Status-Label an, die nach 3 Sekunden verschwindet.
        """
        self.status_message_label.setText(message)
        QTimer.singleShot(3000, lambda: self.status_message_label.setText(""))


    def save_highscore(self, map_name, score, raw_time_seconds, time_bonus):
        """
        Speichert einen Highscore in einer Datei für die gegebene Map.
        Format: Datum_Uhrzeit|MapName|Score|AngepassteZeit|Rohzeit|Zeitbonus
        """
        scores_dir = "assets/scores"
        if not os.path.exists(scores_dir):
            os.makedirs(scores_dir)

        filepath = os.path.join(scores_dir, f"{map_name}.dascores")
        
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        final_time_seconds = raw_time_seconds - time_bonus
        if final_time_seconds < 0:
            final_time_seconds = 0

        score_entry = f"{current_datetime}|{map_name}|{score}|{final_time_seconds}|{raw_time_seconds}|{time_bonus}\n"

        try:
            with open(filepath, 'a') as f: # 'a' für append (anhängen)
                f.write(score_entry)
            print(f"Highscore für '{map_name}' gespeichert.")
        except Exception as e:
            print(f"Fehler beim Speichern des Highscores für '{map_name}': {e}")


    def load_and_display_highscores(self):
        """
        Lädt Highscores für die aktuell ausgewählte Map und zeigt sie in der Tabelle an.
        """
        selected_map_file = self.map_selector.currentText()
        if selected_map_file == "Wähle ein Labyrinth..." or selected_map_file == "Keine Labyrinthe gefunden":
            self.highscores_map_label.setText("Highscores für: Keine Map ausgewählt")
            self.highscores_table.setRowCount(0) # Tabelle leeren
            return

        map_name = selected_map_file # Dateiname ist der Map-Name
        scores_filepath = os.path.join("assets", "scores", f"{map_name}.dascores")
        
        self.highscores_map_label.setText(f"Highscores für: {map_name}")
        self.highscores_table.setRowCount(0) # Tabelle leeren vor dem Laden neuer Daten

        if not os.path.exists(scores_filepath):
            QMessageBox.information(self, "Highscores", f"Für die Map '{map_name}' wurden noch keine Highscores gespeichert.")
            return

        scores_data = []
        try:
            with open(scores_filepath, 'r') as f:
                for line in f:
                    parts = line.strip().split('|')
                    if len(parts) == 6:
                        try:
                            date_time_str = parts[0]
                            score = int(parts[2])
                            final_time_seconds = int(parts[3])
                            raw_time_seconds = int(parts[4])
                            time_bonus = int(parts[5])
                            scores_data.append({
                                'datetime': date_time_str,
                                'map_name': parts[1],
                                'score': score,
                                'final_time': final_time_seconds,
                                'raw_time': raw_time_seconds,
                                'time_bonus': time_bonus
                            })
                        except ValueError as ve:
                            print(f"Fehler beim Parsen der Highscore-Zeile (ValueError): {line.strip()} - {ve}")
                        except IndexError as ie:
                            print(f"Fehler beim Parsen der Highscore-Zeile (IndexError): {line.strip()} - {ie}")
                    else:
                        print(f"Ungültiges Highscore-Format gefunden: {line.strip()}")

        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Laden der Highscores", f"Konnte Highscores für '{map_name}' nicht laden: {e}")
            return

        # Sortieren: primär nach angepasster Zeit (aufsteigend), sekundär nach Score (absteigend)
        scores_data.sort(key=lambda x: (x['final_time'], -x['score']))

        self.highscores_table.setRowCount(len(scores_data))
        for row_idx, entry in enumerate(scores_data):
            self.highscores_table.setItem(row_idx, 0, QTableWidgetItem(entry['datetime']))
            self.highscores_table.setItem(row_idx, 1, QTableWidgetItem(entry['map_name'].replace('.map', '')))
            self.highscores_table.setItem(row_idx, 2, QTableWidgetItem(str(entry['score'])))
            
            minutes = entry['final_time'] // 60
            seconds = entry['final_time'] % 60
            self.highscores_table.setItem(row_idx, 3, QTableWidgetItem(f"{minutes:02d}:{seconds:02d}"))
            
            self.highscores_table.setItem(row_idx, 4, QTableWidgetItem(str(entry['time_bonus'])))


    def handle_game_won(self):
        """Wird aufgerufen, wenn das Spiel gewonnen wurde, zeigt eine Nachricht an und setzt das Spiel zurück."""
        self.timer.stop()
        self.ai_timer.stop() # Stoppt den AI-Timer
        
        final_score = self.maze_logic.get_current_score()
        time_bonus = self.maze_logic.get_end_time_bonus()
        raw_time_seconds = self.game_time_seconds

        selected_map_file = self.map_selector.currentText()
        if selected_map_file != "Wähle ein Labyrinth..." and selected_map_file != "Keine Labyrinthe gefunden":
            self.save_highscore(selected_map_file, final_score, raw_time_seconds, time_bonus)

        final_time_seconds = raw_time_seconds - time_bonus
        if final_time_seconds < 0:
            final_time_seconds = 0

        final_minutes = final_time_seconds // 60
        final_seconds = final_time_seconds % 60

        QMessageBox.information(self, "Spiel gewonnen!",
                                f"Herzlichen Glückwunsch! Du hast das Labyrinth geschafft!\n"
                                f"Gesammelte Enten: {self.maze_logic.get_collected_ducks_count()}/{self.maze_logic.get_total_rewards_count()}\n"
                                f"Dein Score: {final_score} Punkte\n"
                                f"Ursprüngliche Zeit: {raw_time_seconds // 60:02d}:{raw_time_seconds % 60:02d}\n"
                                f"Zeitbonus durch Enten: {time_bonus} Sekunden\n"
                                f"Angepasste Zeit: {final_minutes:02d}:{final_seconds:02d}")
        
        # Wenn KI gesteuert, bleibe auf dem Spielbildschirm und zeige Restart-Button
        if self.maze_logic.is_ai_controlled:
            self.restart_ai_episode_button.show()
        else:
            self.maze_logic.game_over = True # Nur für manuelle Spiele zurücksetzen
            self.show_start_screen()

    def handle_game_lost(self):
        """Wird aufgerufen, wenn das Spiel verloren wurde (Punktestand unter -100)."""
        self.timer.stop()
        self.ai_timer.stop() # Stoppt den AI-Timer
        
        final_score = self.maze_logic.get_current_score()
        QMessageBox.information(self, "Spiel verloren!",
                                f"Dein Punktestand ist unter {self.maze_logic.LOSS_THRESHOLD} gefallen!\n"
                                f"Endgültiger Score: {final_score} Punkte.\n"
                                f"Versuche es noch einmal!")
        
        # Wenn KI gesteuert, bleibe auf dem Spielbildschirm und zeige Restart-Button
        if self.maze_logic.is_ai_controlled:
            self.restart_ai_episode_button.show()
        else:
            self.maze_logic.game_over = True # Nur für manuelle Spiele zurücksetzen
            self.show_start_screen()
