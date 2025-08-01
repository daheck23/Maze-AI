# game/maze_logic.py
import os
from PyQt6.QtCore import pyqtSignal, QObject

class MazeLogic(QObject):
    keys_changed = pyqtSignal(int)
    ducks_changed = pyqtSignal(int)
    game_won = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.maze_data = []
        self.car_position = (0, 0)
        self.door_position = (0, 0)
        self.key_positions = []
        self.reward_positions = [] # Für Enten
        self.collected_keys = 0
        self.collected_rewards = 0
        self.total_keys = 0
        self.total_rewards = 0
        self.game_over = False

    def load_maze_from_file(self, filepath):
        self.reset_game_state() # Immer zurücksetzen beim Laden einer neuen Map
        try:
            with open(filepath, 'r') as f:
                self.maze_data = [list(line.strip()) for line in f if line.strip()]
            
            # Finde Start, Tür, Schlüssel und Enten
            for r, row in enumerate(self.maze_data):
                for c, char in enumerate(row):
                    if char == 'S':
                        self.car_position = (r, c)
                        self.maze_data[r][c] = ' ' # Startposition wird zu einem leeren Pfad
                    elif char == 'E':
                        self.door_position = (r, c)
                        self.maze_data[r][c] = ' ' # Türposition wird zu einem leeren Pfad
                    elif char == 'K':
                        self.key_positions.append((r, c))
                        self.total_keys += 1
                    elif char == 'D':
                        self.reward_positions.append((r, c))
                        self.total_rewards += 1
            
            # Überprüfe, ob S und E gefunden wurden
            if self.car_position == (0,0) and self.door_position == (0,0):
                 print(f"Fehler: Start (S) oder Ende (E) nicht im Labyrinth gefunden: {filepath}")
                 # Fallback: Versuche, Start/Ende in der Mitte/Ecke zu setzen, falls nicht gefunden
                 # Dies ist nur ein Notfall-Fallback und sollte nicht die Norm sein
                 if not any('S' in row for row in self.maze_data):
                     self.car_position = (1, 1) # Beispiel Start oben links
                     self.maze_data[1][1] = ' '
                 if not any('E' in row for row in self.maze_data):
                     self.door_position = (len(self.maze_data) - 2, len(self.maze_data[0]) - 2) # Beispiel Ende unten rechts
                     self.maze_data[len(self.maze_data) - 2][len(self.maze_data[0]) - 2] = ' '
                     
            self.keys_changed.emit(self.collected_keys)
            self.ducks_changed.emit(self.collected_rewards)
            return True
        except FileNotFoundError:
            print(f"Fehler: Die Datei '{filepath}' wurde nicht gefunden.")
            return False
        except Exception as e:
            print(f"Fehler beim Laden des Labyrinths von '{filepath}': {e}")
            return False

    def reset_game_state(self):
        self.maze_data = []
        self.car_position = (0, 0)
        self.door_position = (0, 0)
        self.key_positions = []
        self.reward_positions = []
        self.collected_keys = 0
        self.collected_rewards = 0
        self.total_keys = 0
        self.total_rewards = 0
        self.game_over = False

    def get_maze_data(self):
        return ["".join(row) for row in self.maze_data] # Als Liste von Strings zurückgeben

    def get_car_position(self):
        return self.car_position

    def get_door_position(self):
        return self.door_position

    def get_key_positions(self):
        return self.key_positions

    def get_reward_positions(self):
        return self.reward_positions

    def get_collected_keys_count(self):
        return self.collected_keys

    def get_collected_ducks_count(self):
        return self.collected_rewards

    def is_game_over(self):
        return self.game_over

    def move_car(self, new_row, new_col):
        if self.game_over:
            return False

        rows = len(self.maze_data)
        cols = len(self.maze_data[0])

        # Grenzen prüfen
        if not (0 <= new_row < rows and 0 <= new_col < cols):
            return False

        target_cell = self.maze_data[new_row][new_col]

        if target_cell == 'W': # Wand
            return False
        
        # Bewegung ist gültig
        self.car_position = (new_row, new_col)

        # Schlüssel einsammeln
        if self.car_position in self.key_positions:
            self.key_positions.remove(self.car_position)
            self.collected_keys += 1
            self.keys_changed.emit(self.collected_keys)
            
        # Enten (Belohnungen) einsammeln
        if self.car_position in self.reward_positions:
            self.reward_positions.remove(self.car_position)
            self.collected_rewards += 1
            self.ducks_changed.emit(self.collected_rewards)

        # Ziel erreichen
        if self.car_position == self.door_position:
            if self.collected_keys == self.total_keys:
                self.game_over = True
                self.game_won.emit()
            else:
                # Spieler an der Tür, aber nicht alle Schlüssel gesammelt
                pass # Bleibt an der Tür, kann aber nicht entkommen
        return True