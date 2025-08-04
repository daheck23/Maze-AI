# game/maze_logic.py
# Diese Datei enthält die grundlegende Spiellogik.

import os
import random
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox # Für Meldungen im Spiel (wird nur noch für Spielende verwendet)

class MazeLogic(QObject):
    # Signale, die von der Logik an die Benutzeroberfläche gesendet werden.
    maze_updated = pyqtSignal() # Signalisiert, dass das Labyrinth neu gezeichnet werden muss
    keys_changed = pyqtSignal(int) # Signalisiert eine Änderung der Schlüsselanzahl
    ducks_changed = pyqtSignal(int) # Signalisiert eine Änderung der Entenanzahl
    game_won = pyqtSignal() # Signalisiert, dass das Spiel gewonnen wurde
    game_lost = pyqtSignal() # Signalisiert, dass das Spiel verloren wurde
    message_display_requested = pyqtSignal(str) # Signal für temporäre Nachrichten im UI

    # Konstanten für das Punktesystem
    STARTING_SCORE = 100 
    WALL_HIT_PENALTY = 5
    STEP_PENALTY = 1
    KEY_BONUS = 25
    EXIT_BONUS = 250
    LOSS_THRESHOLD = -100

    # Belohnungswerte für die KI (angepasst für bessere Lernkurve)
    REWARD_STEP = -0.01 # Sehr kleiner Abzug pro Schritt, damit die KI mehr explorieren kann
    REWARD_WALL_HIT = -10.0 # Hoher Abzug für Wandkollision
    REWARD_KEY_COLLECTED = 50.0 # Hohe Belohnung für Schlüssel
    REWARD_DUCK_COLLECTED_BASE = 10.0 # Hohe Belohnung für Enten
    REWARD_EXIT_SUCCESS = 1000.0 # Sehr hohe Belohnung für erfolgreichen Abschluss
    REWARD_EXIT_NO_KEY = -500.0 # Hoher Abzug für Erreichen des Ziels ohne Schlüssel
    REWARD_GAME_LOST = -1000.0 # Sehr hoher Abzug für Spielverlust (Erreichen des LOSS_THRESHOLD)
    REWARD_REVISIT_CELL = -20.0 # Deutlich höherer Abzug für das erneute Besuchen einer Zelle

    def __init__(self):
        super().__init__()
        # Initialisiere die grundlegenden Spielvariablen
        self.maze = [] # Repräsentation des Labyrinths (Liste von Listen von Zeichen)
        self.player_pos = {'x': 0, 'y': 0} # Aktuelle Position des Spielers
        self.start_pos = {'x': 0, 'y': 0} # Speichert die Startposition
        self.collected_keys = set() # Set der gesammelten Schlüssel (z.B. 'key-ruby')
        self.total_keys = 3 # Wir haben immer 3 spezifische Schlüssel (Diamond, Ruby, Saphire)
        self.collected_ducks = 0 # Anzahl der gesammelten Enten
        self.total_rewards = 0 # Gesamtanzahl der Enten, die auf der aktuellen Map platziert wurden
        self.game_over = False # Spielzustand
        self.end_time_bonus = 0 # Zeitbonus durch gesammelte Enten
        self.current_score = self.STARTING_SCORE # Aktueller Punktestand, initialisiert mit Startpunkten
        self.required_exit_key = None # Der Schlüssel, der zum Öffnen der Tür benötigt wird
        self.is_ai_controlled = False # Flag, ob das Spiel von der KI gesteuert wird
        self.original_maze_layout = [] # Speichert das ursprüngliche Labyrinth-Layout für Resets
        self.visited_positions_in_episode = set() # Set zum Speichern besuchter Positionen im aktuellen Durchgang

        # Definition der Enten-Typen und ihrer Werte
        self.duck_types = {
            'duck-gold':    {'char': 'G', 'points': 50, 'time_bonus': 5},
            'duck-pink':    {'char': 'P', 'points': 25, 'time_bonus': 4},
            'duck-red':     {'char': 'R', 'points': 10, 'time_bonus': 3},
            'duck-green':   {'char': 'F', 'points': 5,  'time_bonus': 1}, # 'F' für Green Duck
            'duck-blue':    {'char': 'B', 'points': 1,  'time_bonus': 0},
        }

        # Definition der Schlüssel-Typen
        self.key_types = {
            'key-ruby':    {'char': 'U'}, # 'U' für Ruby Key
            'key-saphire': {'char': 'A'}, # 'A' für Saphire Key
            'key-diamond': {'char': 'I'}, # 'I' für Diamond Key
        }

        # Mapping von Labyrinthzeichen zu numerischen Werten für die KI-Beobachtung
        self.char_to_numeric_map = {
            'W': -1.0,  # Wand
            ' ': 0.0,   # Leerer Pfad
            'S': 0.5,   # Spieler (kann auch 0.0 sein, da Position bekannt ist)
            'E': 1.0,   # Ende/Ziel
            'U': 0.8,   # Rubin-Schlüssel
            'A': 0.8,   # Saphir-Schlüssel
            'I': 0.8,   # Diamant-Schlüssel
            'G': 0.3,   # Gold-Ente
            'P': 0.3,   # Pink-Ente
            'R': 0.3,   # Rote Ente
            'F': 0.3,   # Grüne Ente
            'B': 0.3,   # Blaue Ente
        }
        self.vision_radius = 2 # Die KI "sieht" ein 5x5-Feld um sich herum

    def load_maze_from_file(self, filepath):
        """
        Lädt ein Labyrinth aus einer .map-Datei, validiert es und platziert dynamische Elemente.
        """
        print(f"MazeLogic: Lade Labyrinth von {filepath}")
        if not os.path.exists(filepath):
            print(f"Datei existiert nicht: {filepath}")
            return False

        temp_maze = []
        try:
            with open(filepath, 'r') as f:
                for line_idx, line in enumerate(f):
                    stripped_line = line.rstrip('\n') 
                    if stripped_line:
                        temp_maze.append(list(stripped_line))
        except Exception as e:
            print(f"Fehler beim Lesen der Datei: {e}")
            return False

        if not temp_maze or not temp_maze[0]:
            print("temp_maze ist leer nach dem Lesen der Datei.")
            print("Fehler: Leere Labyrinth-Datei oder ungültiges Format geladen.")
            return False
        
        # Validierung der Zeilenlängen
        width = len(temp_maze[0])
        for r_idx, row in enumerate(temp_maze):
            if len(row) != width:
                print(f"Inkonsistente Zeilenlänge entdeckt! Zeile {r_idx} hat Länge {len(row)}, erwartet {width}.")
                print("Fehler: Ungleichmäßige Zeilenlängen im Labyrinth. Lade nicht.")
                return False
        
        print("Alle Zeilenlängen sind konsistent.")

        # Finde Start- und Endpunkt
        start_found = False
        player_start_x, player_start_y = 0, 0
        end_found = False
        end_x, end_y = 0, 0

        for r_idx, row in enumerate(temp_maze):
            for c_idx, cell in enumerate(row):
                if cell == 'S':
                    player_start_x = c_idx
                    player_start_y = r_idx
                    start_found = True
                elif cell == 'E':
                    end_x = c_idx
                    end_y = r_idx
                    end_found = True
        
        if not start_found:
            print("Fehler: Startpunkt 'S' nicht im Labyrinth gefunden. Lade nicht.")
            return False
        if not end_found:
            print("Fehler: Endpunkt 'E' nicht im Labyrinth gefunden. Lade nicht.")
            return False

        # Speichere das ursprüngliche Labyrinth-Layout
        self.original_maze_layout = [row[:] for row in temp_maze]
        
        # Setze Labyrinth und Spielzustand zurück
        self.maze = [row[:] for row in temp_maze] # Tiefe Kopie des Labyrinths
        self.player_pos = {'x': player_start_x, 'y': player_start_y}
        self.start_pos = {'x': player_start_x, 'y': player_start_y} # Speichere Startposition
        self.collected_keys.clear()
        self.collected_ducks = 0
        self.game_over = False
        self.end_time_bonus = 0
        self.current_score = self.STARTING_SCORE # Setze Punktestand auf Startwert
        self.visited_positions_in_episode.clear() # Besuchte Positionen zurücksetzen
        
        # Wähle zufällig einen Schlüssel, der zum Öffnen der Tür benötigt wird
        self.required_exit_key = random.choice(list(self.key_types.keys()))
        print(f"Für dieses Labyrinth wird der Schlüssel '{self.required_exit_key}' benötigt, um die Tür zu öffnen.")

        # Dynamische Elemente platzieren
        self._place_dynamic_elements()

        # UI-Signale senden
        self.keys_changed.emit(len(self.collected_keys))
        self.ducks_changed.emit(self.collected_ducks)
        self.maze_updated.emit()
        return True

    def _place_dynamic_elements(self):
        """
        Platziert Schlüssel und Enten zufällig auf der aktuell geladenen Map.
        Überprüft, ob die Map bereits Elemente enthält, und platziert nur, wenn nicht.
        """
        height = len(self.maze)
        width = len(self.maze[0])

        # 1. Alle leeren Pfadzellen finden
        all_empty_path_cells = []
        for r in range(height):
            for c in range(width):
                if self.maze[r][c] == ' ': # Nur ' ' Zellen sind potentielle Platzierungsorte
                    all_empty_path_cells.append((r, c))

        # 2. Endposition finden (Startposition ist bereits in self.player_pos)
        end_pos = None
        for r in range(height):
            for c in range(width):
                if self.maze[r][c] == 'E':
                    end_pos = (r, c)
                    break
            if end_pos: break

        # 3. Liste der tatsächlich verfügbaren Zellen erstellen (ohne Start und Ende)
        current_available_cells_for_placement = []
        player_y, player_x = self.player_pos['y'], self.player_pos['x']

        for r, c in all_empty_path_cells:
            if (r, c) != (player_y, player_x) and \
               (r, c) != end_pos:
                current_available_cells_for_placement.append((r, c))
        
        random.shuffle(current_available_cells_for_placement) # Zufällige Reihenfolge

        # Überprüfe, wie viele Schlüssel und Enten bereits auf der Map sind
        # (Dies ist wichtig, wenn Maps geladen werden, die bereits Elemente enthalten)
        current_keys_on_map = set()
        current_ducks_on_map = 0
        
        key_char_to_name = {data['char']: name for name, data in self.key_types.items()}
        duck_char_to_name = {data['char']: name for name, data in self.duck_types.items()}

        for r in range(height):
            for c in range(width):
                cell_content = self.maze[r][c]
                if cell_content in key_char_to_name:
                    current_keys_on_map.add(key_char_to_name[cell_content])
                elif cell_content in duck_char_to_name:
                    current_ducks_on_map += 1

        # Wenn die Map bereits Elemente enthält, verwenden wir diese und platziere keine neuen.
        if current_keys_on_map or current_ducks_on_map:
            print("Info: Labyrinth enthält bereits Schlüssel/Enten. Platziere keine neuen.")
            self.total_keys = len(current_keys_on_map) # Aktualisiere Gesamtschlüssel basierend auf der Map
            self.total_rewards = current_ducks_on_map # Aktualisiere Gesamtenten basierend auf der Map
            return

        # Wenn keine Elemente auf der Map sind, platziere sie neu (wie es der MazeGenerator tun würde)
        # --- Schlüssel platzieren (immer 3) ---
        keys_to_place_chars = [data['char'] for data in self.key_types.values()]

        if len(current_available_cells_for_placement) < len(keys_to_place_chars):
            print(f"WARNUNG: Nicht genügend freie Zellen ({len(current_available_cells_for_placement)}) für alle 3 Schlüssel vorhanden. Es werden nur {len(current_available_cells_for_placement)} Schlüssel platziert.")
            # Platziere so viele Schlüssel wie möglich und entferne sie aus der Liste
            for i in range(len(current_available_cells_for_placement)):
                r, c = current_available_cells_for_placement.pop(0)
                self.maze[r][c] = keys_to_place_chars[i]
            self.total_keys = len(current_available_cells_for_placement) # Anpassung der Gesamtschlüsselanzahl
            self.total_rewards = 0 # Keine Enten, wenn nicht genug Platz für Schlüssel
            return # Frühzeitiger Abbruch

        for key_char in keys_to_place_chars:
            if not current_available_cells_for_placement: # Sicherheitsprüfung
                print("Warnung: Nicht genügend Zellen, um alle Schlüssel zu platzieren. Abbruch der Schlüsselplatzierung.")
                break
            r, c = current_available_cells_for_placement.pop(0)
            self.maze[r][c] = key_char

        # --- Enten platzieren (zufällige Anzahl, an Map-Größe angepasst) ---
        remaining_cells_for_ducks = len(current_available_cells_for_placement)
        min_ducks_guaranteed = 1 # Mindestens eine Ente, wenn Platz ist
        max_ducks_absolute = 25 # Absolute Obergrenze
        
        # Dynamische Berechnung der maximalen Enten, basierend auf den verbleibenden Zellen
        max_ducks_flexible_from_cells = int(remaining_cells_for_ducks * 0.15) # z.B. 15% der freien Zellen
        
        # Die tatsächliche Obergrenze für random.randint
        upper_bound_for_random = min(max_ducks_absolute, max_ducks_flexible_from_cells, remaining_cells_for_ducks)
        
        # Sicherstellen, dass die Untergrenze nicht höher als die Obergrenze ist
        lower_bound_for_random = min_ducks_guaranteed
        if lower_bound_for_random > upper_bound_for_random:
            lower_bound_for_random = upper_bound_for_random
        
        num_ducks_to_place = 0
        if remaining_cells_for_ducks >= lower_bound_for_random: # Nur versuchen, wenn genug Platz für Minimum
            num_ducks_to_place = random.randint(lower_bound_for_random, upper_bound_for_random)

        self.total_rewards = num_ducks_to_place # Aktualisiere Gesamtanzahl der Enten

        duck_chars_to_place = []
        available_duck_types = list(self.duck_types.keys())

        for _ in range(num_ducks_to_place):
            chosen_duck_type = random.choice(available_duck_types)
            duck_chars_to_place.append(self.duck_types[chosen_duck_type]['char'])

        for duck_char in duck_chars_to_place:
            if current_available_cells_for_placement:
                r, c = current_available_cells_for_placement.pop(0)
                self.maze[r][c] = duck_char
            else:
                self.total_rewards = self.collected_ducks # Korrigiere total_rewards basierend auf tatsächlich platzierten
                print(f"WARNUNG: Nicht genügend Pfadzellen für alle Enten vorhanden. Es konnten nur {self.collected_ducks} Enten platziert werden.")
                break

    def move_player(self, dx, dy):
        """
        Bewegt den Spieler im Labyrinth und verarbeitet Kollisionen und das Sammeln von Gegenständen.
        Gibt die Belohnung für diesen Zug und einen 'done'-Flag zurück.
        """
        if self.game_over:
            return 0.0, True # Keine Belohnung, Spiel ist vorbei

        old_x, old_y = self.player_pos['x'], self.player_pos['y'] # Speichere alte Position
        new_x, new_y = old_x + dx, old_y + dy # Berechne neue Position
        reward = self.REWARD_STEP # Standard-Belohnung (kleiner Abzug pro Schritt)
        done = False # Flag, ob das Spiel beendet ist

        # Prüfe Grenzen des Labyrinths
        if not (0 <= new_x < len(self.maze[0]) and 0 <= new_y < len(self.maze)):
            reward = self.REWARD_WALL_HIT # Hoher Abzug für Wandkollision
            self.current_score -= self.WALL_HIT_PENALTY
            self.maze_updated.emit()
            if self.current_score <= self.LOSS_THRESHOLD:
                self.game_over = True
                self.game_lost.emit()
                done = True
            return reward, done # Keine Bewegung bei Wandkollision

        target_cell_char = self.maze[new_y][new_x] # Zeichen der Zielzelle

        if target_cell_char == 'W': # Wand
            reward = self.REWARD_WALL_HIT # Hoher Abzug für Wandkollision
            self.current_score -= self.WALL_HIT_PENALTY
            self.maze_updated.emit()
            if self.current_score <= self.LOSS_THRESHOLD:
                self.game_over = True
                self.game_lost.emit()
                done = True
            return reward, done # Keine Bewegung bei Wandkollision

        # Belohnung für das erneute Besuchen einer Zelle
        if (new_y, new_x) in self.visited_positions_in_episode:
            reward += self.REWARD_REVISIT_CELL # HIER WIRD DIE STRAFE ANGEWENDET
            # print(f"DEBUG: Zelle ({new_x},{new_y}) erneut besucht. Belohnung: {reward}")


        # Gültige Bewegung: Punkteabzug pro Schritt
        self.current_score -= self.STEP_PENALTY

        # Aktualisiere das Labyrinth-Gitter: alte Position leeren, neue Position markieren
        # HINWEIS: Das alte Spielerzeichen 'S' wird immer durch ' ' ersetzt,
        # auch wenn ein Objekt gesammelt wurde. Das Objekt wird dann im nächsten Schritt
        # durch das neue Spielerzeichen 'S' übermalt.
        # Dies ist die korrekte Logik, da der Spieler die Zelle verlässt.
        self.maze[old_y][old_x] = ' ' 
        
        # Spielerposition aktualisieren
        self.player_pos['x'] = new_x
        self.player_pos['y'] = new_y

        # Füge die neue Position zu den besuchten Zellen hinzu
        self.visited_positions_in_episode.add((new_y, new_x))

        # Prüfe, ob ein Schlüssel gesammelt wurde (dies muss NACH der Spielerbewegung erfolgen,
        # damit der Schlüssel auf der Zelle, die der Spieler betritt, erkannt wird)
        key_chars = {data['char']: name for name, data in self.key_types.items()}
        if target_cell_char in key_chars:
            collected_key_name = key_chars[target_cell_char]
            if collected_key_name not in self.collected_keys: # Nur sammeln, wenn noch nicht gesammelt
                self.collected_keys.add(collected_key_name)
                self.current_score += self.KEY_BONUS # Punktebonus für Schlüssel
                reward += self.REWARD_KEY_COLLECTED # Belohnung für Schlüssel
                self.keys_changed.emit(len(self.collected_keys)) # UI aktualisieren
                print(f"Schlüssel {collected_key_name} gesammelt. Insgesamt: {len(self.collected_keys)}")

        # Prüfe, ob eine Ente gesammelt wurde (dies muss NACH der Spielerbewegung erfolgen)
        duck_chars = {data['char']: name for name, data in self.duck_types.items()}
        if target_cell_char in duck_chars:
            collected_duck_name = duck_chars[target_cell_char]
            duck_data = self.duck_types[collected_duck_name]
            
            self.current_score += duck_data['points'] # Punkte hinzufügen
            self.end_time_bonus += duck_data['time_bonus'] # Zeitbonus hinzufügen
            self.collected_ducks += 1 # Anzahl der gesammelten Enten erhöhen
            reward += self.REWARD_DUCK_COLLECTED_BASE + (duck_data['time_bonus'] * 0.5) # Belohnung für Ente
            self.ducks_changed.emit(self.collected_ducks) # UI aktualisieren
            print(f"Ente gesammelt: {collected_duck_name}. Punkte: {self.current_score}, Zeitbonus: {self.end_time_bonus}s")

        # Setze die neue Spielerposition im Labyrinth-Gitter
        # Dies geschieht ZULETZT, damit der Spieler über gesammelten Gegenständen liegt.
        # Wenn die Zielzelle eine Tür ist, wird sie nur dann durch 'S' ersetzt, wenn der richtige Schlüssel da ist.
        if target_cell_char == 'E': # Ende erreicht (Tür)
            if self.required_exit_key in self.collected_keys:
                self.current_score += self.EXIT_BONUS
                reward += self.REWARD_EXIT_SUCCESS # Hohe Belohnung für erfolgreichen Abschluss
                self.game_over = True
                self.game_won.emit()
                done = True
                # Tür verschwindet, da das Spiel gewonnen wurde
                self.maze[new_y][new_x] = 'S' # Spieler steht auf dem ehemaligen Türfeld
            else:
                # Falscher Schlüssel: Tür bleibt sichtbar, Spiel geht weiter, negative Belohnung
                reward += self.REWARD_EXIT_NO_KEY # Abzug für Erreichen des Ziels ohne Schlüssel
                # Die Tür bleibt als 'E' im Labyrinth-Gitter
                self.maze[new_y][new_x] = 'S' # Spieler steht auf dem Türfeld
                self.message_display_requested.emit(f"Falscher Schlüssel! Benötigt: {self.required_exit_key.replace('key-', '').capitalize()}")
                print(f"Falscher Schlüssel! Benötigt: {self.required_exit_key.replace('key-', '').capitalize()}")
                # game_over bleibt False, done bleibt False, damit das Spiel weitergeht
        else:
            # Normale Bewegung: Spieler auf neue Zelle setzen
            self.maze[new_y][new_x] = 'S'


        self.maze_updated.emit() # Signal, dass das Labyrinth neu gezeichnet werden muss (inkl. Punktestand)

        # Prüfe nach jeder Bewegung, ob Spiel verloren ist
        if self.current_score <= self.LOSS_THRESHOLD:
            self.game_over = True
            self.game_lost.emit()
            reward = self.REWARD_GAME_LOST # Sehr hoher Abzug für Spielverlust
            done = True
        
        return reward, done

    def get_state_representation(self):
        """
        Gibt eine numerische Repräsentation des Labyrinths um den Spieler zurück.
        Dies ist der 'Zustand' für das neuronale Netzwerk.
        """
        height = len(self.maze)
        width = len(self.maze[0])
        p_x, p_y = self.player_pos['x'], self.player_pos['y']
        
        state_list = []
        for r_offset in range(-self.vision_radius, self.vision_radius + 1):
            # HIER WURDE vision_offset ZU vision_radius KORRIGIERT
            for c_offset in range(-self.vision_radius, self.vision_radius + 1): 
                cell_x, cell_y = p_x + c_offset, p_y + r_offset
                
                if 0 <= cell_x < width and 0 <= cell_y < height:
                    cell_char = self.maze[cell_y][cell_x]
                    # Wenn die Zelle der Spieler selbst ist, verwenden wir einen spezifischen Wert
                    if r_offset == 0 and c_offset == 0:
                        state_list.append(self.char_to_numeric_map['S'])
                    else:
                        state_list.append(self.char_to_numeric_map.get(cell_char, 0.0)) # Standardwert 0.0 für Unbekannt
                else:
                    state_list.append(self.char_to_numeric_map['W']) # Außerhalb des Labyrinths als Wand behandeln
        return state_list

    def reset_game_for_ai_training(self):
        """
        Setzt das Spiel für einen neuen KI-Trainingsdurchgang zurück,
        ohne die Map neu zu laden.
        """
        print("DEBUG: Spiel für KI-Training zurückgesetzt.")
        # Labyrinth auf den ursprünglichen Zustand zurücksetzen
        self.maze = [row[:] for row in self.original_maze_layout]
        
        # Spielerposition zurücksetzen
        self.player_pos = {'x': self.start_pos['x'], 'y': self.start_pos['y']}
        self.maze[self.player_pos['y']][self.player_pos['x']] = 'S' # Spieler am Startpunkt setzen

        # Gesammelte Gegenstände und Boni zurücksetzen
        self.collected_keys.clear()
        self.collected_ducks = 0
        self.end_time_bonus = 0
        self.current_score = self.STARTING_SCORE
        self.game_over = False
        self.visited_positions_in_episode.clear() # Besuchte Positionen zurücksetzen

        # Wähle zufällig einen NEUEN Schlüssel für diesen Durchgang
        self.required_exit_key = random.choice(list(self.key_types.keys()))
        print(f"DEBUG: Neuer benötigter Schlüssel für KI-Durchgang: '{self.required_exit_key}'")

        # Dynamische Elemente neu platzieren
        self._place_dynamic_elements()

        # UI-Signale senden
        self.keys_changed.emit(len(self.collected_keys))
        self.ducks_changed.emit(self.collected_ducks)
        self.maze_updated.emit() # Labyrinth neu zeichnen
        print("DEBUG: MazeLogic Reset abgeschlossen.")


    def get_maze_data(self):
        """Gibt die aktuelle Labyrinthdaten zurück."""
        return self.maze

    def get_player_pos(self):
        """Gibt die aktuelle Spielerposition zurück."""
        return self.player_pos

    def get_collected_keys_count(self):
        """Gibt die Anzahl der gesammelten Schlüssel zurück."""
        return len(self.collected_keys)

    def get_collected_ducks_count(self):
        """Gibt die Anzahl der gesammelten Enten zurück."""
        return self.collected_ducks
    
    def get_total_rewards_count(self):
        """Gibt die Gesamtanzahl der Enten auf der Map zurück."""
        return self.total_rewards

    def get_end_time_bonus(self):
        """Gibt den aktuellen Zeitbonus durch gesammelte Enten zurück."""
        return self.end_time_bonus

    def get_current_score(self):
        """Gibt den aktuellen Punktestand zurück."""
        return self.current_score

    def is_game_over(self):
        """Prüft, ob das Spiel beendet ist."""
        return self.game_over

    def get_is_ai_controlled(self):
        """Gibt zurück, ob das Spiel von der KI gesteuert wird."""
        return self.is_ai_controlled
