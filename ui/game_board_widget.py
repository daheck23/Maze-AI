# ui/game_board_widget.py
# Dieses Widget ist für die grafische Darstellung des Labyrinths zuständig.

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap, QColor
from PyQt6.QtCore import Qt, QRectF
import os

class GameBoardWidget(QWidget):
    def __init__(self, maze_logic, parent=None):
        super().__init__(parent)
        self.maze_logic = maze_logic # Referenz zur Spiellogik
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Ermöglicht das Empfangen von Tastatureingaben

        self.images = {} # Dictionary zum Speichern der geladenen Bilder
        self.load_images() # Lade alle benötigten Bilder beim Start
        
        # Verbinde das Signal von MazeLogic, um das Widget neu zu zeichnen,
        # wenn sich das Labyrinth oder der Spielerstatus ändert.
        self.maze_logic.maze_updated.connect(self.update)

        # Zuordnung von Labyrinthzeichen zu Bild-Dateinamen
        # Dies ist eine initiale Zuordnung und kann später erweitert werden.
        self.char_to_image_map = {
            'W': 'brickwall.png', # Wand
            ' ': None,            # Leerer Pfad (wird nur als weiße Fläche gezeichnet)
            'S': 'car.png',       # Startpunkt / Spieler
            'E': 'door.png',      # Endpunkt / Tür

            # Platzhalter für Schlüssel und Enten (werden später aktiv genutzt)
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
        
        # Liste aller Bilddateien, die geladen werden sollen.
        # Diese Liste sollte alle Bilder enthalten, die in char_to_image_map verwendet werden.
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
                    print(f"DEBUG: Bild konnte nicht geladen werden oder ist leer: {filepath}")
            else:
                print(f"DEBUG: Bilddatei nicht gefunden: {filepath}")

    def paintEvent(self, event):
        """
        Wird aufgerufen, wenn das Widget neu gezeichnet werden muss.
        Zeichnet das Labyrinth, den Spieler und alle Elemente.
        """
        painter = QPainter(self)
        maze = self.maze_logic.get_maze_data() # Aktuelle Labyrinthdaten von MazeLogic
        player_pos = self.maze_logic.get_player_pos() # Aktuelle Spielerposition

        if not maze or not maze[0]: # Prüfe, ob Labyrinthdaten vorhanden sind
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Kein Labyrinth geladen.")
            return

        # Berechne die Größe jeder Zelle basierend auf der Widget-Größe und Labyrinth-Dimensionen
        cell_width = self.width() // len(maze[0])
        cell_height = self.height() // len(maze)

        # Durchlaufe jede Zelle des Labyrinths und zeichne sie
        for r_idx, row in enumerate(maze):
            for c_idx, cell in enumerate(row):
                # Zeichne zuerst den Hintergrund der Zelle (Wand oder Pfad)
                if cell == 'W':
                    painter.fillRect(c_idx * cell_width, r_idx * cell_height, cell_width, cell_height, QColor('gray'))
                else: # Pfad oder ein Element darauf
                    painter.fillRect(c_idx * cell_width, r_idx * cell_height, cell_width, cell_height, QColor('white'))

                target_image = None
                # Finde den passenden Bilddateinamen für das aktuelle Labyrinthzeichen
                if cell in self.char_to_image_map and self.char_to_image_map[cell] is not None:
                    image_filename = self.char_to_image_map[cell]
                    target_image = self.images.get(image_filename)
                
                # Wenn ein Bild gefunden wurde, zeichne es skaliert und zentriert in der Zelle
                if target_image:
                    scaled_image = target_image.scaled(cell_width, cell_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    x_offset = (cell_width - scaled_image.width()) // 2
                    y_offset = (cell_height - scaled_image.height()) // 2
                    painter.drawPixmap(c_idx * cell_width + x_offset, r_idx * cell_height + y_offset, scaled_image)
                
                # Der Spieler wird durch das 'S'-Zeichen und das 'car.png'-Bild repräsentiert.
                # Eine separate Zeichnung ist hier nicht nötig, da 'S' bereits gemappt ist.
                pass 

    def keyPressEvent(self, event):
        """
        Behandelt Tastatureingaben für die Spielerbewegung.
        """
        # Wenn das Spiel vorbei ist, ignoriere Tastatureingaben
        if self.maze_logic.is_game_over():
            return

        # Rufe die move_player-Methode in MazeLogic auf, basierend auf der gedrückten Taste
        if event.key() == Qt.Key.Key_W:
            self.maze_logic.move_player(0, -1) # Hoch
        elif event.key() == Qt.Key.Key_S:
            self.maze_logic.move_player(0, 1)  # Runter
        elif event.key() == Qt.Key.Key_A:
            self.maze_logic.move_player(-1, 0) # Links
        elif event.key() == Qt.Key.Key_D:
            self.maze_logic.move_player(1, 0)  # Rechts
        else:
            # Standardbehandlung für andere Tasten, die nicht relevant sind
            super().keyPressEvent(event)
