# ui/maze_generator.py
# Diese Klasse ist für die Generierung von Labyrinthen zuständig.

import random

class MazeGenerator:
    def __init__(self):
        pass

    def generate_maze(self, inner_width, inner_height):
        """
        Generiert ein Labyrinth mit einem Prim-ähnlichen Algorithmus,
        inklusive einer umlaufenden äußeren Mauer.

        Args:
            inner_width (int): Die gewünschte Breite des INNEREN, spielbaren Labyrinths.
            inner_height (int): Die gewünschte Höhe des INNEREN, spielbaren Labyrinths.

        Returns:
            list[list[str]]: Das generierte Labyrinth-Gitter mit äußerer Mauer.
        """
        # Die tatsächliche Größe des Gitters wird 2 größer sein als die innere Größe,
        # um Platz für die umlaufende Mauer zu schaffen.
        grid_width = inner_width + 2
        grid_height = inner_height + 2

        # Initialisiere das gesamte Gitter mit Wänden ('W')
        grid = [['W' for _ in range(grid_width)] for _ in range(grid_height)]

        # Wähle einen zufälligen Startpunkt für den Prim-Algorithmus
        # Dieser Punkt muss im INNEREN Bereich des Labyrinths liegen (nicht auf der äußeren Mauer)
        # und muss ungerade Koordinaten haben (wenn wir ein Gitter von Zellen und Wänden betrachten).
        # Hier wählen wir einfach einen zufälligen Punkt innerhalb des inneren Bereichs.
        start_y = random.randrange(1, inner_height + 1) # +1 weil 0-indiziert und bis inner_height+1
        start_x = random.randrange(1, inner_width + 1)   # +1 weil 0-indiziert und bis inner_width+1

        # Stelle sicher, dass der Startpunkt ungerade Indizes hat, wenn wir ein "Zellen"-Gitter wollen
        # Dies ist wichtig für den Prim-Algorithmus, um saubere Pfade zu erzeugen.
        # Wenn wir einfach zufällige Pfade auf einem Gitter von Wänden und Pfaden erzeugen,
        # können wir auch gerade Indizes verwenden. Hier wird einfach der Startpunkt zum Pfad gemacht.
        grid[start_y][start_x] = ' ' # Mache den Startpunkt zum Pfad

        walls = []
        # Füge die Wände um den Startpunkt zur Liste der zu verarbeitenden Wände hinzu.
        # Diese Wände sind die, die den Startpunkt von angrenzenden unbesuchten Zellen trennen.
        self._add_walls(grid, start_x, start_y, walls, grid_width, grid_height)

        while walls:
            # Wähle eine zufällige Wand aus der Liste und entferne sie
            wall_idx = random.randrange(len(walls))
            wall_x, wall_y = walls.pop(wall_idx)

            # Prüfe die 4 Nachbarzellen der Wand, um die unbesuchte Zelle zu finden
            # (dx, dy) sind die Richtungen: (0,1)=unten, (0,-1)=oben, (1,0)=rechts, (-1,0)=links
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] 

            found_connection = False
            for dx, dy in directions:
                # Berechne die Koordinaten der Zellen auf beiden Seiten der Wand
                cell_on_one_side_x, cell_on_one_side_y = wall_x - dx, wall_y - dy
                cell_on_other_side_x, cell_on_other_side_y = wall_x + dx, wall_y + dy

                # Überprüfen, ob die Zellen gültig sind (innerhalb der Grenzen des GESAMTEN Gitters)
                # und ob die Wand genau einen Pfad (' ') und eine unbesuchte Wandzelle ('W') trennt.
                if (0 <= cell_on_one_side_y < grid_height and 0 <= cell_on_one_side_x < grid_width and \
                    grid[cell_on_one_side_y][cell_on_one_side_x] == ' ') and \
                   (0 <= cell_on_other_side_y < grid_height and 0 <= cell_on_other_side_x < grid_width and \
                    grid[cell_on_other_side_y][cell_on_other_side_x] == 'W'):

                    # Wir haben eine Wand gefunden, die einen Pfad mit einer unbesuchten Wand verbindet
                    grid[wall_y][wall_x] = ' ' # Mache die Wand (aktuell wall_x, wall_y) zum Pfad
                    grid[cell_on_other_side_y][cell_on_other_side_x] = ' ' # Mache die unbesuchte Zelle zum Pfad
                    # Füge die neuen Wände um die neu besuchte Zelle zur Liste hinzu
                    self._add_walls(grid, cell_on_other_side_x, cell_on_other_side_y, walls, grid_width, grid_height) 
                    found_connection = True
                    break # Nur eine solche Verbindung pro Wand verarbeiten

        return grid

    def _add_walls(self, grid, x, y, walls, grid_width, grid_height):
        """
        Fügt die umliegenden Wände einer Zelle zur Liste der zu verarbeitenden Wände hinzu.
        """
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Unten, Oben, Rechts, Links
        
        for dx, dy in directions:
            wx, wy = x + dx, y + dy # Wand-Kandidat

            # Prüfe, ob die Wand innerhalb der Grenzen des GESAMTEN Gitters liegt
            # und tatsächlich eine Wand ist ('W').
            if 0 <= wy < grid_height and 0 <= wx < grid_width and grid[wy][wx] == 'W':
                # Nur hinzufügen, wenn die Wand noch nicht in der Liste ist, um Duplikate zu vermeiden.
                if (wx, wy) not in walls: 
                    walls.append((wx, wy))


    def add_elements_to_maze(self, maze_data):
        """
        Fügt Start (S) und Ende (E) zu einem generierten Labyrinth hinzu.
        Diese Elemente werden IMMER innerhalb der äußeren Mauer platziert.
        """
        height = len(maze_data)
        width = len(maze_data[0])

        # Finde alle leeren Pfadzellen, die potentiell für S und E verwendet werden können.
        # Wichtig: Nur Zellen INNERHALB der äußeren Mauer berücksichtigen.
        available_cells = []
        for r in range(1, height - 1): # Start bei 1, Ende bei height-2 (um äußere Mauer zu ignorieren)
            for c in range(1, width - 1): # Start bei 1, Ende bei width-2 (um äußere Mauer zu ignorieren)
                if maze_data[r][c] == ' ':
                    available_cells.append((r, c))
        
        if not available_cells:
            print("FEHLER: Kein Platz für Start/Ende im Labyrinth gefunden (alle Wände?).")
            return maze_data # Gebe das Labyrinth unverändert zurück, da es unspielbar wäre.

        random.shuffle(available_cells) # Mische die verfügbaren Zellen für zufällige Platzierung

        # Platziere Startpunkt 'S'
        if available_cells:
            start_y, start_x = available_cells.pop()
            maze_data[start_y][start_x] = 'S'
        else:
            print("Warnung: Nicht genügend Platz für Startpunkt 'S'.")
            return maze_data # Frühzeitiger Abbruch, wenn S nicht platziert werden kann

        # Platziere Endpunkt 'E'
        if available_cells: # Sicherstellen, dass noch Zellen für 'E' verfügbar sind
            end_y, end_x = available_cells.pop()
            maze_data[end_y][end_x] = 'E'
        else:
            print("Warnung: Nicht genügend Platz für Endpunkt 'E' nach Platzierung von 'S'.")
            # Fallback: Versuche, den Endpunkt direkt neben dem Startpunkt zu setzen, wenn kein anderer Pfad da ist
            possible_end_neighbors = []
            for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Nachbarrichtungen
                nx, ny = start_x + dx, start_y + dy
                # Prüfe, ob Nachbar innerhalb der Grenzen des INNEREN Bereichs liegt
                # und keine Wand oder der Startpunkt selbst ist.
                if (1 <= ny < height - 1 and 1 <= nx < width - 1) and \
                   maze_data[ny][nx] != 'W' and \
                   maze_data[ny][nx] != 'S': # Nicht den Startpunkt selbst überschreiben
                    possible_end_neighbors.append((ny, nx))
            if possible_end_neighbors:
                end_y, end_x = random.choice(possible_end_neighbors)
                maze_data[end_y][end_x] = 'E'
            else:
                print("Konnte keinen Platz für Endpunkt 'E' finden, selbst neben 'S'.")

        return maze_data
