# ui/game_board_widget.py
# Dieses Widget ist für die grafische Darstellung des Labyrinths zuständig.

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap, QColor
from PyQt6.QtCore import Qt, QRectF, QTimer 
import os # NEU: Importiere das os-Modul

class GameBoardWidget(QWidget):
    def __init__(self, maze_logic, parent=None):
        super().__init__(parent)
        self.maze_logic = maze_logic # Referenz zur Spiellogik
        # Das FocusPolicy wird jetzt von MainWindow gesteuert, je nachdem, ob AI spielt
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) 
        print(f"DEBUG: GameBoardWidget __init__: Initial FocusPolicy = {self.focusPolicy()}")

        self.images = {} # Dictionary zum Speichern der geladenen Bilder
        self.load_images() # Lade alle benötigten Bilder beim Start
        
        # Verbinde das Signal von MazeLogic, um das Widget neu zu zeichnen,
        # wenn sich das Labyrinth oder der Spielerstatus ändert.
        self.maze_logic.maze_updated.connect(self.update)
        
        # Setze die Ränder auf 0, um sicherzustellen, dass das Widget den gesamten Platz nutzt
        self.setContentsMargins(0, 0, 0, 0)

        # Zuordnung von Labyrinthzeichen zu Bild-Dateinamen
        self.char_to_image_map = {
            'W': 'brickwall.png', # Wand
            ' ': None,            # Leerer Pfad (wird nur als weiße Fläche gezeichnet)
            'S': 'car.png',       # Startpunkt / Spieler
            'E': 'door.png',      # Endpunkt / Tür

            # Schlüssel und Enten
            'U': 'key-ruby.png',
            'A': 'key-saphire.png',
            'I': 'key-diamond.png',
            'G': 'duck-gold.png',
            'P': 'duck-pink.png',
            'R': 'duck-red.png',
            'F': 'duck-green.png',
            'B': 'duck-blue.png',
        }

    def load_images(self):
        """
        Lädt alle benötigten Bilddateien aus dem 'assets/images'-Ordner.
        Gibt Warnungen aus, wenn Dateien nicht gefunden oder nicht geladen werden können.
        """
        image_dir = "assets/images"
        
        image_files = [
            'brickwall.png', 'car.png', 'door.png',
            'key-diamond.png', 'key-saphire.png', 'key-ruby.png',
            'duck-gold.png', 'duck-red.png', 'duck-blue.png', 'duck-green.png', 'duck-pink.png'
        ]

        for filename in image_files:
            filepath = os.path.join(image_dir, filename)
            if os.path.exists(filepath):
                pixmap = QPixmap(filepath)
                if not pixmap.isNull():
                    self.images[filename] = pixmap
                else:
                    print(f"Bild konnte nicht geladen werden oder ist leer: {filepath}")
            else:
                print(f"Bilddatei nicht gefunden: {filepath}")

    def paintEvent(self, event):
        """
        Wird aufgerufen, wenn das Widget neu gezeichnet werden muss.
        Zeichnet das Labyrinth, den Spieler und alle Elemente.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # Für glattere Linien
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform) # Für glattere Bildskalierung

        maze = self.maze_logic.get_maze_data() # Aktuelle Labyrinthdaten von MazeLogic

        if not maze or not maze[0]: # Prüfe, ob Labyrinthdaten vorhanden sind
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Kein Labyrinth geladen.")
            return

        maze_width_cells = len(maze[0])
        maze_height_cells = len(maze)

        # Berechne die Größe jeder Zelle, um das gesamte Labyrinth passend und quadratisch darzustellen
        available_width = self.width()
        available_height = self.height()

        # Debug-Ausgaben zur Diagnose des Skalierungsproblems
        # print(f"DEBUG: paintEvent - Widget size: {available_width}x{available_height}")
        # print(f"DEBUG: paintEvent - Maze size: {maze_width_cells}x{maze_height_cells}")

        cell_size_by_width = available_width / maze_width_cells
        cell_size_by_height = available_height / maze_height_cells

        # Wähle die kleinere der beiden Seiten, um sicherzustellen, dass das gesamte Labyrinth passt
        cell_size = min(cell_size_by_width, cell_size_by_height)
        
        # print(f"DEBUG: paintEvent - Calculated cell_size: {cell_size}")

        # Berechne Offsets, um das Labyrinth im Widget zu zentrieren
        total_maze_pixel_width = maze_width_cells * cell_size
        total_maze_pixel_height = maze_height_cells * cell_size

        start_x = (available_width - total_maze_pixel_width) / 2
        start_y = (available_height - total_maze_pixel_height) / 2

        # Debug-Ausgaben für Zentrierung
        # print(f"DEBUG: paintEvent - Start X: {start_x}, Start Y: {start_y}")
        # print(f"DEBUG: paintEvent - Total Maze Pixel Size: {total_maze_pixel_width}x{total_maze_pixel_height}")

        # Durchlaufe jede Zelle des Labyrinths und zeichne sie
        for r_idx, row in enumerate(maze):
            for c_idx, cell in enumerate(row):
                x = start_x + c_idx * cell_size
                y = start_y + r_idx * cell_size

                # Zeichne zuerst den Hintergrund der Zelle (Wand oder Pfad)
                if cell == 'W':
                    painter.fillRect(int(x), int(y), int(cell_size), int(cell_size), QColor('gray'))
                else: # Pfad oder ein Element darauf
                    painter.fillRect(int(x), int(y), int(cell_size), int(cell_size), QColor('white'))

                target_image = None
                # Finde den passenden Bilddateinamen für das aktuelle Labyrinthzeichen
                if cell in self.char_to_image_map and self.char_to_image_map[cell] is not None:
                    image_filename = self.char_to_image_map[cell]
                    target_image = self.images.get(image_filename)
                
                # Wenn ein Bild gefunden wurde, zeichne es skaliert und zentriert in der Zelle
                if target_image:
                    scaled_image = target_image.scaled(int(cell_size), int(cell_size), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    x_offset = (int(cell_size) - scaled_image.width()) // 2
                    y_offset = (int(cell_size) - scaled_image.height()) // 2
                    painter.drawPixmap(int(x + x_offset), int(y + y_offset), scaled_image)
                
                # Der Spieler wird durch das 'S'-Zeichen und das 'car.png'-Bild repräsentiert.
                # Eine separate Zeichnung ist hier nicht nötig, da 'S' bereits gemappt ist.
                pass 

        # Debug-Rahmen um das gezeichnete Labyrinth
        painter.setPen(QColor('blue'))
        painter.drawRect(int(start_x), int(start_y), int(total_maze_pixel_width), int(total_maze_pixel_height))


    def keyPressEvent(self, event):
        """
        Behandelt Tastatureingaben für die Spielerbewegung.
        """
        # print(f"DEBUG: keyPressEvent triggered! Key: {event.key()} (is_ai_controlled: {self.maze_logic.is_ai_controlled})")
        
        if self.maze_logic.is_ai_controlled:
            # print("DEBUG: KI-Steuerung aktiv, Tastatureingabe ignoriert.")
            return

        if self.maze_logic.is_game_over():
            # print("DEBUG: Spiel vorbei, Tastatureingabe ignoriert.")
            return

        if event.key() == Qt.Key.Key_W:
            self.maze_logic.move_player(0, -1) # Hoch
        elif event.key() == Qt.Key.Key_S:
            self.maze_logic.move_player(0, 1)  # Runter
        elif event.key() == Qt.Key.Key_A:
            self.maze_logic.move_player(-1, 0) # Links
        elif event.key() == Qt.Key.Key_D:
            self.maze_logic.move_player(1, 0)  # Rechts
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        """
        Wird aufgerufen, wenn das Widget den Fokus erhält.
        """
        print("DEBUG: GameBoardWidget hat den Fokus erhalten.")
        super().focusInEvent(event)

    def resizeEvent(self, event):
        """
        Wird aufgerufen, wenn die Größe des Widgets geändert wird.
        Erzwingt ein Neuzeichnen, um die Labyrinthskalierung anzupassen.
        """
        self.update() # Erzwingt ein Neuzeichnen
        super().resizeEvent(event)
