# game/maze_generator.py
import random
import os

class MazeGenerator:
    def __init__(self):
        pass

    def generate_maze(self, width, height):
        """
        Generiert ein Labyrinth mit dem Recursive Backtracker Algorithmus.
        Das Labyrinth ist zunächst mit Wänden gefüllt ('W').
        Die Wände werden später zu Pfaden (' ') umgewandelt.
        Die Breite und Höhe müssen ungerade sein, um Korridore und Wände zu ermöglichen.
        """
        if width % 2 == 0: width += 1
        if height % 2 == 0: height += 1

        # Initialisiere das Gitter mit Wänden
        maze = [['W' for _ in range(width)] for _ in range(height)]

        # Startpunkt für die Generierung
        start_x, start_y = 1, 1 
        maze[start_y][start_x] = ' ' # Startzelle ist ein Pfad

        visited = set()
        stack = [(start_y, start_x)]
        visited.add((start_y, start_x))

        while stack:
            current_y, current_x = stack[-1] # Aktuelle Zelle ist die oberste auf dem Stack
            
            # Finde unbesuchte Nachbarn (nur die "Zellen", nicht die "Wände" dazwischen)
            unvisited_neighbors = []
            # (dy, dx) Paare für Oben, Unten, Links, Rechts (mit 2er-Schritten)
            for dy, dx in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
                ny, nx = current_y + dy, current_x + dx
                if 1 <= ny < height - 1 and 1 <= nx < width - 1 and (ny, nx) not in visited:
                    unvisited_neighbors.append((ny, nx))
            
            if unvisited_neighbors:
                # Wähle einen zufälligen unbesuchten Nachbarn
                next_y, next_x = random.choice(unvisited_neighbors)

                # Entferne die Wand zwischen aktueller und nächster Zelle
                # Die Wand ist immer genau in der Mitte
                wall_y, wall_x = (current_y + next_y) // 2, (current_x + next_x) // 2
                maze[wall_y][wall_x] = ' ' # Wand wird zu Pfad

                maze[next_y][next_x] = ' ' # Nächste Zelle ist jetzt auch ein Pfad
                visited.add((next_y, next_x))
                stack.append((next_y, next_x)) # Füge die neue Zelle zum Stack hinzu
            else:
                stack.pop() # Keine unbesuchten Nachbarn, gehe einen Schritt zurück
        
        return ["".join(row) for row in maze] # Gib als Liste von Strings zurück

    def add_elements_to_maze(self, maze_rows, num_keys=1, num_ducks=0):
        """
        Platziert Start (S), Ende (E), Schlüssel (K) und Enten (D) im generierten Labyrinth.
        Stellt sicher, dass S und E an den Rändern liegen und K/D auf Pfaden.
        """
        height = len(maze_rows)
        width = len(maze_rows[0])
        maze = [list(row) for row in maze_rows] # Wandle in Liste von Listen um zur Bearbeitung

        path_cells = []
        for r in range(height):
            for c in range(width):
                if maze[r][c] == ' ':
                    path_cells.append((r, c))
        
        # Sicherstellen, dass S und E an gegenüberliegenden Ecken sind und auf Pfaden liegen
        # Wähle zufällig eine der vier Ecken als Start
        corners = [
            (1, 1), (1, width - 2), 
            (height - 2, 1), (height - 2, width - 2)
        ]
        
        # Filtere Ecken, die keine Pfade sind (sollten eigentlich immer Pfade sein in dieser Implementierung)
        valid_corners = [c for c in corners if maze[c[0]][c[1]] == ' ']
        if not valid_corners:
            # Fallback, wenn keine Ecken als Pfad verfügbar sind (sehr unwahrscheinlich bei korrektem Maze-Algorithmus)
            # Wähle stattdessen zufällige Pfadzellen
            if len(path_cells) < 2:
                raise ValueError("Nicht genügend Pfadzellen für Start und Ende.")
            start_pos = path_cells.pop(random.randrange(len(path_cells)))
            end_pos = path_cells.pop(random.randrange(len(path_cells)))
        else:
            start_pos = random.choice(valid_corners)
            # Finde die gegenüberliegende Ecke für das Ende
            if start_pos == (1, 1): end_pos = (height - 2, width - 2)
            elif start_pos == (1, width - 2): end_pos = (height - 2, 1)
            elif start_pos == (height - 2, 1): end_pos = (1, width - 2)
            else: end_pos = (1, 1)

            # Prüfe, ob die gegenüberliegende Ecke auch ein Pfad ist
            if maze[end_pos[0]][end_pos[1]] != ' ':
                # Wenn nicht, wähle eine andere zufällige Pfadzelle
                # (Sollte nicht passieren, wenn der Maze-Algorithmus ein durchgehendes Labyrinth erzeugt)
                if len(path_cells) < 1:
                    raise ValueError("Nicht genügend Pfadzellen für Ende.")
                end_pos = path_cells.pop(random.randrange(len(path_cells)))

        maze[start_pos[0]][start_pos[1]] = 'S'
        maze[end_pos[0]][end_pos[1]] = 'E'

        # Entferne Start- und Endpositionen aus den möglichen Pfadzellen für K/D
        if start_pos in path_cells: path_cells.remove(start_pos)
        if end_pos in path_cells: path_cells.remove(end_pos)

        # Platziere Schlüssel und Enten
        elements_to_place = []
        for _ in range(num_keys): elements_to_place.append('K')
        for _ in range(num_ducks): elements_to_place.append('D')

        random.shuffle(elements_to_place)

        for element_char in elements_to_place:
            if path_cells:
                idx = random.randrange(len(path_cells))
                r, c = path_cells.pop(idx) # Nehmen und entfernen, damit keine Doppelbelegung
                maze[r][c] = element_char
            else:
                print(f"Warnung: Nicht genügend Pfadzellen für {element_char} vorhanden.")

        return ["".join(row) for row in maze]

    def save_maze_to_file(self, maze_data, filename="generated_maze.map", folder="assets/maps"):
        """Speichert das generierte Labyrinth in einer .map-Datei."""
        if not os.path.exists(folder):
            os.makedirs(folder)
        filepath = os.path.join(folder, filename)
        with open(filepath, 'w') as f:
            for row in maze_data:
                f.write(row + '\n')
        return filepath # Gibt den vollen Pfad zurück