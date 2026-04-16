from abc import ABC, abstractmethod


class Tetromino(ABC):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.rotation = 0
        self._matrix = self._get_matrices()  # Fix #1: cache once, reuse in get_image

    @abstractmethod
    def _get_matrices(self):
        pass

    def get_image(self):
        # Fix #1: use cached self._matrix instead of recomputing every call
        return self._matrix[self.rotation % len(self._matrix)]


class Board:
    def __init__(self):
        self.width = 10
        self.height = 20
        self.grid = [[(0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]

    def is_valid_pos(self, shape, adj_x=0, adj_y=0):
        """Checks if the piece's next position is within bounds and not overlapping."""
        for px, py in shape.get_image():
            # Fix #5: use round() instead of int() to avoid float truncation drift
            nx = round(shape.x + px + adj_x)
            ny = round(shape.y + py + adj_y)

            # Check floor and walls
            if nx < 0 or nx >= self.width or ny >= self.height:
                return False
            # Check if the cell is already taken (ignoring off-screen start)
            if ny >= 0 and self.grid[ny][nx] != (0, 0, 0):
                return False
        return True

    def lock_shape(self, shape):
        for px, py in shape.get_image():
            ny, nx = round(shape.y + py), round(shape.x + px)  # Fix #5: round() here too
            if 0 <= ny < self.height:
                self.grid[ny][nx] = shape.color

    def clear_lines(self):
        """Remove full rows and shift everything above down."""
        # Fix #2: rebuild grid instead of mutating while iterating (prevents row-skip bug)
        # Fix #3: use self.width instead of hardcoded 10
        new_grid = [row for row in self.grid if (0, 0, 0) in row]
        lines_cleared = len(self.grid) - len(new_grid)
        for _ in range(lines_cleared):
            new_grid.insert(0, [(0, 0, 0) for _ in range(self.width)])
        self.grid = new_grid
        return lines_cleared


class ShapeDot(Tetromino):
    def _get_matrices(self):
        return [[(0, 0)]]


class ShapeI(Tetromino):
    def _get_matrices(self):
        return [
            [(0, 1), (1, 1), (2, 1), (3, 1)],
            [(2, 0), (2, 1), (2, 2), (2, 3)],
        ]


class ShapeT(Tetromino):
    def _get_matrices(self):
        return [
            [(1, 0), (0, 1), (1, 1), (2, 1)],  # Up
            [(1, 0), (1, 1), (1, 2), (2, 1)],  # Right
            [(0, 1), (1, 1), (2, 1), (1, 2)],  # Down
            [(1, 0), (0, 1), (1, 1), (1, 2)],  # Left
        ]


class ShapeL(Tetromino):
    def _get_matrices(self):
        return [
            [(0, 1), (1, 1), (2, 1), (2, 0)],
            [(1, 0), (1, 1), (1, 2), (2, 2)],
            [(0, 1), (1, 1), (2, 1), (0, 2)],
            [(0, 0), (1, 0), (1, 1), (1, 2)],  # Fix #4: corrected rotation state 3
        ]


class ShapeO(Tetromino):
    def _get_matrices(self):
        return [[(0, 0), (1, 0), (0, 1), (1, 1)]]