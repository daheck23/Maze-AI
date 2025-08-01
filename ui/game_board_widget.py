from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt, QSize, QPoint

from game.maze_logic import MazeLogic

class GameBoardWidget(QWidget):
    def __init__(self, maze_logic_instance, parent=None):
        super().__init__(parent)
        self.maze_logic = maze_logic_instance
        self.setMinimumSize(QSize(600, 600))

        self.cell_size = 50

        self.wall_image = None
        self.car_image = None
        self.key_image = None
        self.duck_image = None
        self.door_image = None

        self.load_assets()

        self.fallback_wall_color = QColor(100, 100, 100)
        self.fallback_car_color = QColor(0, 0, 255)
        self.fallback_key_color = QColor(255, 255, 0)
        self.fallback_duck_color = QColor(255, 165, 0)
        self.fallback_door_color = QColor(139, 69, 19)

    def load_assets(self):
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        maze_data = self.maze_logic.get_maze_data()
        
        # --- KORREKTUR HIER: Sicherstellen, dass maze_data nicht leer ist und num_cols korrekt berechnet wird ---
        num_rows = len(maze_data)
        num_cols = 0
        if num_rows > 0:
            # Berechne num_cols basierend auf der Länge der ersten Zeile
            # oder der längsten Zeile, falls Labyrinthe unregelmäßig sein könnten (hier nicht der Fall)
            num_cols = len(maze_data[0]) 

        available_width = self.width()
        available_height = self.height()
        
        if num_cols > 0 and num_rows > 0:
            self.cell_size = max(1, min(available_width // num_cols, available_height // num_rows))
        else:
            self.cell_size = 50 
            # Wenn num_cols oder num_rows 0 sind, können wir nichts zeichnen,
            # außer dem Hintergrund. Das ist wichtig, um den IndexError zu vermeiden.
            painter.fillRect(self.rect(), QColor(50, 50, 50)) # Nur Hintergrund zeichnen
            painter.end()
            return # Frühzeitiger Exit, wenn keine gültigen Labyrinthdaten vorhanden sind

        # Zeichne den Hintergrund des gesamten Widgets
        painter.fillRect(self.rect(), QColor(50, 50, 50))

        # --- Labyrinth-Zeichnung ---
        for r in range(num_rows):
            for c in range(num_cols): # Nun sollte num_cols korrekt sein
                char = maze_data[r][c]
                x = c * self.cell_size
                y = r * self.cell_size

                if char == 'W':
                    painter.fillRect(x, y, self.cell_size, self.cell_size, self.fallback_wall_color)
                else:
                    painter.fillRect(x, y, self.cell_size, self.cell_size, QColor(200, 200, 200))
                
                painter.setPen(QColor(150, 150, 150))
                painter.drawRect(x, y, self.cell_size, self.cell_size)
            
        painter.end()