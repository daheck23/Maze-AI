# ai/agent.py
import random
import torch
import torch.nn as nn
import torch.optim as optim

# Platzhalter für das Neuronale Netzwerk (wird später implementiert)
class SimpleNeuralNetwork(nn.Module):
    def __init__(self, input_size, output_size):
        super(SimpleNeuralNetwork, self).__init__()
        # Dies ist ein minimalistisches Beispiel.
        # Später werden hier Schichten für ein echtes neuronales Netz hinzugefügt.
        self.fc = nn.Linear(input_size, output_size)

    def forward(self, x):
        # Einfache Weiterleitung. Später komplexere Aktivierungen und Schichten.
        return self.fc(x)

class Agent:
    def __init__(self, maze_logic):
        """
        Initialisiert den KI-Agenten.
        Args:
            maze_logic: Eine Instanz von MazeLogic, um auf den Spielzustand zugreifen zu können.
        """
        self.maze_logic = maze_logic
        self.model = None # Platzhalter für das neuronale Netzwerk
        self.optimizer = None
        self.loss_fn = None

        # Definiere mögliche Aktionen: (dx, dy) für Bewegung
        # Die Reihenfolge ist wichtig und muss konsistent sein.
        self.actions = {
            0: (0, -1), # Hoch (W)
            1: (0, 1),  # Runter (S)
            2: (-1, 0), # Links (A)
            3: (1, 0)   # Rechts (D)
        }
        self.num_actions = len(self.actions)

        # Initialisiere ein einfaches Modell (Platzhalter)
        # Die Input-Größe hängt von der Beobachtung des Labyrinths ab (später mehr dazu).
        # Die Output-Größe ist die Anzahl der möglichen Aktionen.
        # Für den Anfang nehmen wir eine Dummy-Input-Größe an.
        dummy_input_size = 10 # Dies wird später durch die tatsächliche Observierungsgröße ersetzt
        self.model = SimpleNeuralNetwork(dummy_input_size, self.num_actions)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.loss_fn = nn.MSELoss()

    def choose_action(self):
        """
        Wählt eine Aktion basierend auf dem aktuellen Zustand des Labyrinths.
        Für den Anfang wählt der Agent eine zufällige, gültige Aktion.
        Später wird hier das neuronale Netzwerk verwendet.
        """
        if self.maze_logic.is_game_over():
            return None # Keine Aktion, wenn das Spiel vorbei ist

        valid_moves = []
        player_x, player_y = self.maze_logic.get_player_pos()['x'], self.maze_logic.get_player_pos()['y']
        maze = self.maze_logic.get_maze_data()

        # Überprüfe, welche Bewegungen gültig sind
        for action_id, (dx, dy) in self.actions.items():
            new_x, new_y = player_x + dx, player_y + dy

            # Prüfe Grenzen
            if 0 <= new_x < len(maze[0]) and 0 <= new_y < len(maze):
                # Prüfe, ob die Zielzelle eine Wand ist
                if maze[new_y][new_x] != 'W':
                    valid_moves.append(action_id)
        
        if not valid_moves:
            # Wenn keine gültigen Züge möglich sind (z.B. komplett eingemauert),
            # wähle eine zufällige Aktion, die gegen eine Wand laufen könnte,
            # oder gib None zurück, um keine Bewegung zu machen.
            # Für den Anfang lassen wir ihn zufällig gegen Wände laufen, um das Punktesystem zu testen.
            return random.choice(list(self.actions.keys())) 
        
        # Wähle eine zufällige gültige Aktion
        chosen_action_id = random.choice(valid_moves)
        print(f"KI wählt Aktion (zufällig): {self.actions[chosen_action_id]}")
        return self.actions[chosen_action_id]

    def learn(self, state, action, reward, next_state, done):
        """
        Platzhalterfunktion für den Lernprozess des Agenten (Reinforcement Learning).
        Wird später implementiert.
        """
        pass
