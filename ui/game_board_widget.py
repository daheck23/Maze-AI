# ui/game_board_widget.py
# Dieses Widget ist für die grafische Darstellung des Labyrinths zuständig.

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap, QColor
from PyQt6.QtCore import Qt, QRectF, QTimer 
import os 

class GameBoardWidget(QWidget):
    def __init__(self, maze_logic, parent=None):
        super().__init__(parent)
        self.maze_logic = maze_logic # Referenz zur Spiellogik
        # Das FocusPolicy wird jetzt von MainWindow gesteuert, je nachdem, ob AI spielt
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) 
        # print(f"DEBUG: GameBoardWidget __init__: Initial FocusPolicy = {self.focusPolicy()}")

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
                    print(f"Image could not be loaded or is empty: {filepath}")
            else:
                print(f"Image file not found: {filepath}")

    def paintEvent(self, event):
        """
        Wird aufgerufen, wenn das Widget neu gezeichnet werden muss.
        Zeichnet das Labyrinth, den Spieler und alle Elemente.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) 
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform) 

        maze = self.maze_logic.get_maze_data() 

        if not maze or not maze[0]: 
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No maze loaded.")
            return

        maze_width_cells = len(maze[0])
        maze_height_cells = len(maze)

        available_width = self.width()
        available_height = self.height()

        # Debug-Ausgaben zur Diagnose des Skalierungsproblems
        print(f"DEBUG: paintEvent - Widget size: {available_width}x{available_height}")
        print(f"DEBUG: paintEvent - Maze dimensions (cells): {maze_width_cells}x{maze_height_cells}")

        cell_size_by_width = available_width / maze_width_cells
        cell_size_by_height = available_height / maze_height_cells

        cell_size = min(cell_size_by_width, cell_size_by_height)
        
        print(f"DEBUG: paintEvent - Calculated cell_size: {cell_size:.2f}")

        total_maze_pixel_width = maze_width_cells * cell_size
        total_maze_pixel_height = maze_height_cells * cell_size

        start_x = (available_width - total_maze_pixel_width) / 2
        start_y = (available_height - total_maze_pixel_height) / 2

        print(f"DEBUG: paintEvent - Total Maze Pixel Size (calculated): {total_maze_pixel_width:.2f}x{total_maze_pixel_height:.2f}")
        print(f"DEBUG: paintEvent - Start drawing coordinates (x,y): ({start_x:.2f}, {start_y:.2f})")

        for r_idx, row in enumerate(maze):
            for c_idx, cell in enumerate(row):
                x = start_x + c_idx * cell_size
                y = start_y + r_idx * cell_size

                if cell == 'W':
                    painter.fillRect(int(x), int(y), int(cell_size), int(cell_size), QColor('gray'))
                else: 
                    painter.fillRect(int(x), int(y), int(cell_size), int(cell_size), QColor('white'))

                target_image = None
                if cell in self.char_to_image_map and self.char_to_image_map[cell] is not None:
                    image_filename = self.char_to_image_map[cell]
                    target_image = self.images.get(image_filename)
                
                if target_image:
                    scaled_image = target_image.scaled(int(cell_size), int(cell_size), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    x_offset = (int(cell_size) - scaled_image.width()) // 2
                    y_offset = (int(cell_size) - scaled_image.height()) // 2
                    painter.drawPixmap(int(x + x_offset), int(y + y_offset), scaled_image)
                
        painter.setPen(QColor('blue'))
        painter.drawRect(int(start_x), int(start_y), int(total_maze_pixel_width), int(total_maze_pixel_height))


    def keyPressEvent(self, event):
        if self.maze_logic.is_ai_controlled:
            return

        if self.maze_logic.is_game_over():
            return

        if event.key() == Qt.Key.Key_W:
            self.maze_logic.move_player(0, -1) 
        elif event.key() == Qt.Key.Key_S:
            self.maze_logic.move_player(0, 1)  
        elif event.key() == Qt.Key.Key_A:
            self.maze_logic.move_player(-1, 0) 
        elif event.key() == Qt.Key.Key_D:
            self.maze_logic.move_player(1, 0)  
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        print("DEBUG: GameBoardWidget has gained focus.")
        super().focusInEvent(event)

    def resizeEvent(self, event):
        self.update() 
        super().resizeEvent(event)
