# ui/game_board_widget.py
from PyQt6.QtWidgets import QWidget # QMessageBox entfernt
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
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def load_assets(self):
        try:
            self.wall_image = QPixmap("assets/images/brickwall.png")
            self.car_image = QPixmap("assets/images/car.png")
            self.key_image = QPixmap("assets/images/key-gold.png")
            self.duck_image = QPixmap("assets/images/duck.png")
            self.door_image = QPixmap("assets/images/door.png")

            if self.wall_image.isNull(): print("DEBUG: brickwall.png konnte nicht geladen werden.")
            if self.car_image.isNull(): print("DEBUG: car.png konnte nicht geladen werden.")
            if self.key_image.isNull(): print("DEBUG: key-gold.png konnte nicht geladen werden.")
            if self.duck_image.isNull(): print("DEBUG: duck.png konnte nicht geladen werden.")
            if self.door_image.isNull(): print("DEBUG: door.png konnte nicht geladen werden. Prüfe Pfad/Datei!")

        except Exception as e:
            print(f"DEBUG: Ein unerwarteter Fehler beim Laden der Assets ist aufgetreten: {e}")
            print("DEBUG: Überprüfe die Pfade und ob die Bilddateien existieren.")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        maze_data = self.maze_logic.get_maze_data()
        
        if not maze_data:
            painter.fillRect(self.rect(), QColor(50, 50, 50))
            painter.end()
            return

        num_rows = len(maze_data)
        num_cols = max(len(row) for row in maze_data)

        available_width = self.width()
        available_height = self.height()
        
        if num_cols > 0 and num_rows > 0:
            self.cell_size = max(1, min(available_width // num_cols, available_height // num_rows))
        else:
            self.cell_size = 50
            painter.fillRect(self.rect(), QColor(50, 50, 50))
            painter.end()
            return

        painter.fillRect(self.rect(), QColor(50, 50, 50))

        draw_size = self.cell_size + 1 

        for r in range(num_rows):
            if r >= len(maze_data) or not isinstance(maze_data[r], str):
                continue

            current_row_len = len(maze_data[r])
            for c in range(num_cols):
                char = ' '
                if c < current_row_len: 
                    char = maze_data[r][c]

                x = c * self.cell_size
                y = r * self.cell_size

                if char == 'W':
                    if self.wall_image and not self.wall_image.isNull():
                        painter.drawPixmap(x, y, draw_size, draw_size, self.wall_image)
                    else:
                        painter.fillRect(x, y, draw_size, draw_size, self.fallback_wall_color)
                else:
                    painter.fillRect(x, y, draw_size, draw_size, QColor(200, 200, 200))
                
        painter.setPen(Qt.PenStyle.NoPen)

        for k_pos in self.maze_logic.get_key_positions():
            x = k_pos[1] * self.cell_size
            y = k_pos[0] * self.cell_size
            if self.key_image and not self.key_image.isNull():
                painter.drawPixmap(x, y, self.cell_size, self.cell_size, self.key_image)
            else:
                painter.setBrush(self.fallback_key_color)
                painter.drawEllipse(x + self.cell_size // 4, y + self.cell_size // 4, self.cell_size // 2, self.cell_size // 2)

        for d_pos in self.maze_logic.get_reward_positions():
            x = d_pos[1] * self.cell_size
            y = d_pos[0] * self.cell_size
            if self.duck_image and not self.duck_image.isNull():
                painter.drawPixmap(x, y, self.cell_size, self.cell_size, self.duck_image)
            else:
                painter.setBrush(self.fallback_duck_color)
                painter.drawRect(x + self.cell_size // 4, y + self.cell_size // 4, self.cell_size // 2, self.cell_size // 2)

        door_pos = self.maze_logic.get_door_position()
        x = door_pos[1] * self.cell_size
        y = door_pos[0] * self.cell_size
        if self.door_image and not self.door_image.isNull():
            painter.drawPixmap(x, y, self.cell_size, self.cell_size, self.door_image)
        else:
            painter.setBrush(self.fallback_door_color)
            painter.drawRect(x, y, self.cell_size, self.cell_size)

        car_pos = self.maze_logic.get_car_position()
        x = car_pos[1] * self.cell_size
        y = car_pos[0] * self.cell_size
        if self.car_image and not self.car_image.isNull():
            painter.drawPixmap(x, y, self.cell_size, self.cell_size, self.car_image)
        else:
            painter.setBrush(self.fallback_car_color)
            painter.drawEllipse(x + self.cell_size // 8, y + self.cell_size // 8, self.cell_size * 3 // 4, self.cell_size * 3 // 4)
            
        painter.end()
    
    def keyPressEvent(self, event):
        if self.maze_logic.is_game_over():
            return

        dx, dy = 0, 0 

        if event.key() == Qt.Key.Key_Left:
            dx = -1
        elif event.key() == Qt.Key.Key_Right:
            dx = 1
        elif event.key() == Qt.Key.Key_Up:
            dy = -1
        elif event.key() == Qt.Key.Key_Down:
            dy = 1
        else:
            super().keyPressEvent(event)
            return

        if dx != 0 or dy != 0:
            current_row, current_col = self.maze_logic.get_car_position()
            new_row, new_col = current_row + dy, current_col + dx
            
            if self.maze_logic.move_car(new_row, new_col):
                self.update()
                
                # QMessageBox für den Sieg wird jetzt von MainWindow gehandhabt
                # if self.maze_logic.is_game_over():
                #     QMessageBox.information(self, "Spiel gewonnen!", "Glückwunsch, du hast alle Schlüssel gesammelt und die Tür erreicht!")