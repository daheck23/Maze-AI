import random

class MazeLogic:
    def __init__(self, rows=9, cols=10):
        self.rows = rows
        self.cols = cols
        self.maze = []
        self.car_position = (0, 0) # Beispielposition, wird später dynamisch
        self.door_position = (0, 0) # Beispielposition, wird später dynamisch
        self.key_positions = [] # Liste von (row, col) Tupeln für Schlüssel
        self.reward_positions = [] # Liste von (row, col) Tupeln für Rubber Ducks
        self.required_key = None # Der Schlüssel, der für die Tür benötigt wird

        self._load_example_maze() # Lädt für den Anfang ein festes Labyrinth

    def _load_example_maze(self):
        # Für den Anfang laden wir ein festes Beispiel-Labyrinth
        # Später wird hier die Logik für das Laden aus .map-Dateien und die Generierung sein
        self.maze = [
            "WWWWWWWWWW",
            "WS       W", # Start (S) ist jetzt drinnen
            "W WWW WW W",
            "W W   W  W",
            "W W WWW WW",
            "W W W    W",
            "W WWWW W W",
            "W   W  WX",  # Ziel (X) ist jetzt drinnen
            "WWWWWWWWWW"
        ]
        # Beispielpositionen setzen (müssen zum Beispiel-Labyrinth passen)
        self.car_position = (1, 1) # Entspricht 'S'
        self.door_position = (7, 8) # Entspricht 'X'

        # Beispiel-Schlüssel und Belohnungen hinzufügen (später zufällig)
        self.key_positions = [(3, 2), (5, 7)] # Zwei Schlüssel
        self.reward_positions = [(2, 8), (6, 1)] # Zwei Rubber Ducks
        self.required_key = "gold" # Beispiel: Goldener Schlüssel wird für die Tür benötigt

    def get_maze_data(self):
        """Gibt die aktuelle Labyrinthstruktur zurück."""
        return self.maze

    def get_car_position(self):
        """Gibt die aktuelle Position des Autos zurück."""
        return self.car_position

    def get_door_position(self):
        """Gibt die Position der Tür zurück."""
        return self.door_position

    def get_key_positions(self):
        """Gibt die Positionen der Schlüssel zurück."""
        return self.key_positions

    def get_reward_positions(self):
        """Gibt die Positionen der Belohnungsobjekte zurück."""
        return self.reward_positions

    def get_required_key(self):
        """Gibt den Typ des für die Tür benötigten Schlüssels zurück."""
        return self.required_key

    # --- Zukünftige Methoden hier hinzufügen: ---
    # def generate_new_map(self): ...
    # def load_map_from_file(self, filename): ...
    # def move_car(self, direction): ...
    # def check_for_collision(self, new_pos): ...
    # def collect_item(self, position): ...
    # def update_game_state(self): ...