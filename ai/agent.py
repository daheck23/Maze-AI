# ai/agent.py
import random
import torch
import torch.nn as nn
import torch.optim as optim
import os

# Definition des Neuronalen Netzwerks (DQN)
class QNetwork(nn.Module):
    def __init__(self, input_size, output_size):
        super(QNetwork, self).__init__()
        # Ein einfaches Feedforward-Netzwerk
        self.fc1 = nn.Linear(input_size, 128)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, output_size)

    def forward(self, x):
        # Sicherstellen, dass der Input ein Float-Tensor ist
        x = x.float() 
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

class Agent:
    def __init__(self, maze_logic, model_path="ai/q_network_model.pth"):
        """
        Initialisiert den KI-Agenten.
        Args:
            maze_logic: Eine Instanz von MazeLogic, um auf den Spielzustand zugreifen zu können.
            model_path: Pfad zum Speichern/Laden des Modells.
        """
        self.maze_logic = maze_logic
        self.model_path = model_path

        # Definiere mögliche Aktionen: (dx, dy) für Bewegung
        # Die Reihenfolge ist wichtig und muss konsistent sein.
        self.actions = {
            0: (0, -1), # Hoch (W)
            1: (0, 1),  # Runter (S)
            2: (-1, 0), # Links (A)
            3: (1, 0)   # Rechts (D)
        }
        self.num_actions = len(self.actions)

        # Bestimme die Input-Größe basierend auf dem Sichtradius des Labyrinths
        # (2 * vision_radius + 1) * (2 * vision_radius + 1)
        self.input_size = (2 * self.maze_logic.vision_radius + 1) ** 2 
        
        self.policy_net = QNetwork(self.input_size, self.num_actions)
        self.target_net = QNetwork(self.input_size, self.num_actions)
        self.target_net.load_state_dict(self.policy_net.state_dict()) # Target-Netzwerk initialisieren
        self.target_net.eval() # Target-Netzwerk in den Evaluierungsmodus setzen

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
        self.loss_fn = nn.MSELoss()

        # Hyperparameter für Reinforcement Learning (Q-Learning)
        self.gamma = 0.99  # Diskontierungsfaktor (bleibt hoch, um zukünftige Belohnungen zu berücksichtigen)
        self.epsilon = 1.0 # Startwert für Exploration (100% Exploration)
        self.epsilon_decay = 0.995 # NEU: Epsilon-Abnahme pro Schritt/Episode (etwas schneller als 0.999)
        self.epsilon_min = 0.05 # Minimaler Epsilon-Wert (mindestens 5% Exploration)

    def choose_action(self, state, last_move_resulted_in_wall_hit=False, last_move_vector=None):
        """
        Wählt eine Aktion basierend auf dem aktuellen Zustand (epsilon-greedy).
        Verhindert, dass die KI sofort in eine Wand zurückgeht, wenn der letzte Zug eine Wand traf.
        Args:
            state: Die numerische Repräsentation des aktuellen Zustands (Liste).
            last_move_resulted_in_wall_hit: True, wenn der vorherige Zug eine Wand traf.
            last_move_vector: Der Vektor des vorherigen Zuges (dx, dy).
        Returns:
            Ein Tupel (dx, dy) der gewählten Bewegung.
        """
        # Konvertiere den Zustand in einen PyTorch-Tensor
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0) # Unsqueeze für Batch-Dimension

        # Bestimme die umgekehrte Aktion, die vermieden werden soll
        reverse_action_id = -1
        if last_move_resulted_in_wall_hit and last_move_vector is not None:
            rev_dx, rev_dy = -last_move_vector[0], -last_move_vector[1]
            for idx, (adx, ady) in self.actions.items():
                if adx == rev_dx and ady == rev_dy:
                    reverse_action_id = idx
                    break

        # Epsilon-Greedy-Strategie: Zufällige Aktion (Exploration) oder beste Aktion (Exploitation)
        if random.random() < self.epsilon:
            # Exploration: Wähle eine zufällige gültige Aktion
            valid_moves = []
            player_x, player_y = self.maze_logic.get_player_pos()['x'], self.maze_logic.get_player_pos()['y']
            maze = self.maze_logic.get_maze_data()

            for action_id, (dx, dy) in self.actions.items():
                new_x, new_y = player_x + dx, player_y + dy
                if 0 <= new_x < len(maze[0]) and 0 <= new_y < len(maze) and maze[new_y][new_x] != 'W':
                    valid_moves.append(action_id)
            
            # Vermeide sofortige Rückkehr in eine Wand, wenn es andere Optionen gibt
            if reverse_action_id != -1 and reverse_action_id in valid_moves and len(valid_moves) > 1:
                valid_moves.remove(reverse_action_id)
                # print(f"DEBUG: Exploration: Umgekehrte Aktion {self.actions[reverse_action_id]} vermieden.")

            if valid_moves:
                chosen_action_id = random.choice(valid_moves)
            else:
                # Fallback: Wenn keine anderen gültigen Züge möglich sind, muss die KI eventuell doch zurück
                chosen_action_id = random.choice(list(self.actions.keys())) # Wähle zufällig, auch wenn es die Rückwärtsbewegung ist
                # print("DEBUG: Exploration: Keine anderen gültigen Züge, musste eventuell umgekehrte Aktion wählen.")
            
            return self.actions[chosen_action_id]
        else:
            # Exploitation: Wähle die Aktion mit dem höchsten Q-Wert vom Policy-Netzwerk
            with torch.no_grad(): # Keine Gradientenberechnung für die Vorhersage
                q_values = self.policy_net(state_tensor)
                # Sortiere Aktionen nach Q-Werten absteigend
                sorted_q_values, sorted_action_ids = torch.sort(q_values, descending=True)
                sorted_action_ids = sorted_action_ids.squeeze().tolist() # Konvertiere zu Liste

            chosen_action_id = -1
            player_x, player_y = self.maze_logic.get_player_pos()['x'], self.maze_logic.get_player_pos()['y']
            maze = self.maze_logic.get_maze_data()

            # Iteriere durch die Aktionen in der Reihenfolge ihrer Q-Werte
            for action_id in sorted_action_ids:
                dx, dy = self.actions[action_id]
                new_x, new_y = player_x + dx, player_y + dy

                is_valid_move = (0 <= new_x < len(maze[0]) and 0 <= new_y < len(maze) and maze[new_y][new_x] != 'W')
                is_reverse_move = (action_id == reverse_action_id)

                if is_valid_move:
                    # Wenn es die umgekehrte Aktion ist und die letzte Bewegung eine Wand traf,
                    # und es gibt noch andere gültige Optionen, überspringe diese.
                    if is_reverse_move and last_move_resulted_in_wall_hit and len([a for a in sorted_action_ids if a != action_id]) > 0:
                        # print(f"DEBUG: Exploitation: Umgekehrte Aktion {self.actions[action_id]} vermieden.")
                        continue # Versuche die nächste beste Aktion
                    else:
                        chosen_action_id = action_id
                        break # Beste gültige Aktion gefunden
            
            if chosen_action_id == -1: # Fallback, falls alle bevorzugten Aktionen ungültig/vermieden wurden
                # Wähle eine zufällige gültige Aktion
                valid_moves = []
                for action_id, (dx_v, dy_v) in self.actions.items():
                    new_x_v, new_y_v = player_x + dx_v, player_y + dy_v
                    if 0 <= new_x_v < len(maze[0]) and 0 <= new_y_v < len(maze) and maze[new_y_v][new_x_v] != 'W':
                        valid_moves.append(action_id)
                if valid_moves:
                    chosen_action_id = random.choice(valid_moves)
                    # print("DEBUG: Exploitation: Fallback zu zufälliger gültiger Aktion.")
                else:
                    chosen_action_id = random.choice(list(self.actions.keys())) # Letzter Ausweg
                    # print("DEBUG: Exploitation: Keine gültigen Züge, musste zufällig wählen.")

            return self.actions[chosen_action_id]

    def learn(self, state, action_idx, reward, next_state, done):
        """
        Führt einen Lernschritt für das Q-Netzwerk durch.
        Args:
            state: Der Zustand VOR der Aktion.
            action_idx: Der Index der ausgeführten Aktion.
            reward: Die erhaltene Belohnung.
            next_state: Der Zustand NACH der Aktion.
            done: True, wenn der nächste Zustand ein Endzustand ist.
        """
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        action_tensor = torch.tensor([action_idx], dtype=torch.long).unsqueeze(0)
        reward_tensor = torch.tensor([reward], dtype=torch.float32).unsqueeze(0)
        next_state_tensor = torch.tensor(next_state, dtype=torch.float32).unsqueeze(0)
        done_tensor = torch.tensor([done], dtype=torch.bool).unsqueeze(0)

        # Berechne Q-Werte für den aktuellen Zustand (Q(s,a))
        current_q_values = self.policy_net(state_tensor).gather(1, action_tensor)

        # Berechne die maximalen Q-Werte für den nächsten Zustand (max Q(s',a'))
        # Wenn der nächste Zustand ein Endzustand ist, ist der Ziel-Q-Wert nur die Belohnung
        next_q_values = torch.zeros(1, dtype=torch.float32)
        if not done:
            next_q_values = self.target_net(next_state_tensor).max(1)[0].detach()
        
        # Berechne den erwarteten Q-Wert (Ziel-Q-Wert)
        expected_q_values = reward_tensor + (self.gamma * next_q_values)

        # Berechne den Verlust und führe Backpropagation durch
        loss = self.loss_fn(current_q_values, expected_q_values.unsqueeze(1))
        
        self.optimizer.zero_grad()
        loss.backward()
        # Optional: Gradient Clipping, um Gradientenexplosion zu verhindern
        # for param in self.policy_net.parameters():
        #     param.grad.data.clamp_(-1, 1)
        self.optimizer.step()

        # Epsilon Decay (Abnahme der Exploration)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # Aktualisiere das Target-Netzwerk (periodisch oder nach jedem Lernschritt)
        # Für einfache Implementierung aktualisieren wir es hier nach jedem Schritt
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        return loss.item() # Gibt den Verlustwert zurück

    def save_model(self):
        """Speichert den Zustand des Policy-Netzwerks."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save(self.policy_net.state_dict(), self.model_path)
        print(f"KI-Modell erfolgreich gespeichert unter: {self.model_path}")

    def load_model(self):
        """Lädt einen gespeicherten Zustand in das Policy-Netzwerk."""
        if os.path.exists(self.model_path):
            try:
                self.policy_net.load_state_dict(torch.load(self.model_path))
                self.target_net.load_state_dict(self.policy_net.state_dict())
                print(f"KI-Modell erfolgreich geladen von: {self.model_path}")
                # Optional: Epsilon nach dem Laden anpassen, um nicht bei 1.0 zu starten
                self.epsilon = max(self.epsilon_min, self.epsilon * 0.5) # Z.B. auf die Hälfte des aktuellen Epsilon setzen, aber nicht unter min
                print(f"Epsilon nach Laden angepasst auf: {self.epsilon:.4f}")
            except Exception as e:
                print(f"Fehler beim Laden des KI-Modells von {self.model_path}: {e}")
                print("Starte mit einem neuen, untrainierten Modell.")
        else:
            print(f"Kein KI-Modell unter {self.model_path} gefunden. Starte mit einem neuen Modell.")

    def get_action_index(self, dx, dy):
        """Hilfsfunktion: Gibt den Index einer Aktion basierend auf (dx, dy) zurück."""
        for idx, (adx, ady) in self.actions.items():
            if adx == dx and ady == dy:
                return idx
        return -1 # Sollte nicht passieren
