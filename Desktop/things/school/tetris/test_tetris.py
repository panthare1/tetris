import unittest
import pygame
from unittest.mock import patch

from logic import Board, ShapeI, ShapeT, ShapeL, ShapeO, ShapeDot
from factory import ShapeFactory
from settings import Settings, DEFAULT_BINDINGS


BLACK = (0, 0, 0)
RED   = (220, 0, 0)


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

class TestBoardInit(unittest.TestCase):

    def setUp(self):
        self.board = Board()

    def test_grid_height(self):
        self.assertEqual(len(self.board.grid), 20)

    def test_grid_width(self):
        for row in self.board.grid:
            self.assertEqual(len(row), 10)

    def test_grid_starts_empty(self):
        for row in self.board.grid:
            for cell in row:
                self.assertEqual(cell, BLACK)


class TestBoardIsValidPos(unittest.TestCase):

    def setUp(self):
        self.board = Board()
        self.piece = ShapeO(3, 0, RED)   # 2×2 block at (3, 0)

    def test_center_is_valid(self):
        self.assertTrue(self.board.is_valid_pos(self.piece))

    def test_left_wall_blocks(self):
        self.piece.x = -1
        self.assertFalse(self.board.is_valid_pos(self.piece))

    def test_right_wall_blocks(self):
        self.piece.x = 9          # O-piece is 2 wide → col 10 out of bounds
        self.assertFalse(self.board.is_valid_pos(self.piece))

    def test_floor_blocks(self):
        self.piece.y = 20         # cells at y=20 are off the bottom
        self.assertFalse(self.board.is_valid_pos(self.piece))

    def test_adj_x_left_valid(self):
        self.piece.x = 1
        self.assertTrue(self.board.is_valid_pos(self.piece, adj_x=-1))

    def test_adj_x_into_wall_invalid(self):
        self.piece.x = 0
        self.assertFalse(self.board.is_valid_pos(self.piece, adj_x=-1))

    def test_adj_y_into_floor_invalid(self):
        self.piece.y = 19
        self.assertFalse(self.board.is_valid_pos(self.piece, adj_y=1))

    def test_blocked_by_existing_cell(self):
        self.board.grid[1][3] = RED
        self.piece.x, self.piece.y = 3, 0
        self.assertFalse(self.board.is_valid_pos(self.piece, adj_y=1))


class TestBoardLockShape(unittest.TestCase):

    def setUp(self):
        self.board = Board()

    def test_lock_writes_color(self):
        piece = ShapeO(0, 0, RED)
        self.board.lock_shape(piece)
        self.assertEqual(self.board.grid[0][0], RED)
        self.assertEqual(self.board.grid[0][1], RED)
        self.assertEqual(self.board.grid[1][0], RED)
        self.assertEqual(self.board.grid[1][1], RED)

    def test_lock_dot_single_cell(self):
        piece = ShapeDot(5, 5, RED)
        self.board.lock_shape(piece)
        self.assertEqual(self.board.grid[5][5], RED)

    def test_lock_does_not_affect_other_cells(self):
        piece = ShapeDot(5, 5, RED)
        self.board.lock_shape(piece)
        self.assertEqual(self.board.grid[0][0], BLACK)


class TestBoardClearLines(unittest.TestCase):

    def setUp(self):
        self.board = Board()

    def _fill_row(self, row_index):
        self.board.grid[row_index] = [RED] * self.board.width

    def test_no_full_rows_returns_zero(self):
        self.assertEqual(self.board.clear_lines(), 0)

    def test_one_full_row_returns_one(self):
        self._fill_row(19)
        self.assertEqual(self.board.clear_lines(), 1)

    def test_two_full_rows_returns_two(self):
        self._fill_row(18)
        self._fill_row(19)
        self.assertEqual(self.board.clear_lines(), 2)

    def test_cleared_row_is_replaced_by_empty_row(self):
        self._fill_row(19)
        self.board.clear_lines()
        self.assertEqual(self.board.grid[0], [BLACK] * self.board.width)

    def test_grid_height_unchanged_after_clear(self):
        self._fill_row(19)
        self.board.clear_lines()
        self.assertEqual(len(self.board.grid), 20)

    def test_rows_shift_down_after_clear(self):
        # place a marker in row 18, fill row 19 fully
        self.board.grid[18][0] = RED
        self._fill_row(19)
        self.board.clear_lines()
        # marker should have moved to row 19
        self.assertEqual(self.board.grid[19][0], RED)


# ---------------------------------------------------------------------------
# Tetromino shapes
# ---------------------------------------------------------------------------

class TestShapeI(unittest.TestCase):

    def setUp(self):
        self.piece = ShapeI(0, 0, RED)

    def test_has_two_rotations(self):
        self.assertEqual(len(self.piece._matrix), 2)

    def test_default_rotation_is_horizontal(self):
        cells = self.piece.get_image()
        ys = [py for _, py in cells]
        self.assertTrue(all(y == ys[0] for y in ys), "All y-values should be equal (horizontal)")

    def test_rotation_1_is_vertical(self):
        self.piece.rotation = 1
        cells = self.piece.get_image()
        xs = [px for px, _ in cells]
        self.assertTrue(all(x == xs[0] for x in xs), "All x-values should be equal (vertical)")

    def test_rotation_wraps(self):
        self.piece.rotation = 2
        self.assertEqual(self.piece.get_image(), self.piece._matrix[0])


class TestShapeO(unittest.TestCase):

    def setUp(self):
        self.piece = ShapeO(0, 0, RED)

    def test_has_one_rotation(self):
        self.assertEqual(len(self.piece._matrix), 1)

    def test_is_2x2(self):
        self.assertEqual(len(self.piece.get_image()), 4)

    def test_rotation_unchanged(self):
        self.piece.rotation = 99
        self.assertEqual(self.piece.get_image(), self.piece._matrix[0])


class TestShapeT(unittest.TestCase):

    def setUp(self):
        self.piece = ShapeT(0, 0, RED)

    def test_has_four_rotations(self):
        self.assertEqual(len(self.piece._matrix), 4)

    def test_each_rotation_has_four_cells(self):
        for i in range(4):
            self.piece.rotation = i
            self.assertEqual(len(self.piece.get_image()), 4)


class TestShapeL(unittest.TestCase):

    def setUp(self):
        self.piece = ShapeL(0, 0, RED)

    def test_has_four_rotations(self):
        self.assertEqual(len(self.piece._matrix), 4)

    def test_each_rotation_has_four_cells(self):
        for i in range(4):
            self.piece.rotation = i
            self.assertEqual(len(self.piece.get_image()), 4)


class TestShapeDot(unittest.TestCase):

    def setUp(self):
        self.piece = ShapeDot(5, 5, RED)

    def test_single_cell(self):
        self.assertEqual(self.piece.get_image(), [(0, 0)])

    def test_position_stored(self):
        self.assertEqual(self.piece.x, 5)
        self.assertEqual(self.piece.y, 5)


# ---------------------------------------------------------------------------
# ShapeFactory
# ---------------------------------------------------------------------------

class TestShapeFactory(unittest.TestCase):

    def test_returns_tetromino_subclass(self):
        from logic import Tetromino
        piece = ShapeFactory.get_random_shape()
        self.assertIsInstance(piece, Tetromino)

    def test_color_is_rgb_tuple(self):
        piece = ShapeFactory.get_random_shape()
        self.assertIsInstance(piece.color, tuple)
        self.assertEqual(len(piece.color), 3)

    def test_starts_near_top(self):
        piece = ShapeFactory.get_random_shape()
        self.assertEqual(piece.y, 0)

    def test_produces_multiple_shape_types(self):
        types = {type(ShapeFactory.get_random_shape()) for _ in range(50)}
        self.assertGreater(len(types), 1)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettings(unittest.TestCase):

    def test_default_bindings_has_all_actions(self):
        required = {"Move Left", "Move Right", "Soft Drop", "Rotate", "Pause", "Hard Drop"}
        self.assertTrue(required.issubset(DEFAULT_BINDINGS.keys()))

    def test_default_bindings_values_are_ints(self):
        for action, keycode in DEFAULT_BINDINGS.items():
            self.assertIsInstance(keycode, int, f"{action} keycode should be int")

    @patch("settings.load_bindings", return_value=dict(DEFAULT_BINDINGS))
    def test_settings_getitem_returns_keycode(self, _mock):
        s = Settings()
        self.assertEqual(s["Move Left"], DEFAULT_BINDINGS["Move Left"])

    @patch("settings.load_bindings", return_value=dict(DEFAULT_BINDINGS))
    def test_settings_all_actions_accessible(self, _mock):
        s = Settings()
        for action in DEFAULT_BINDINGS:
            self.assertIsNotNone(s[action])

    @patch("settings.load_bindings", return_value=dict(DEFAULT_BINDINGS))
    def test_settings_reload_updates_bindings(self, mock_load):
        s = Settings()
        new_bindings = dict(DEFAULT_BINDINGS)
        new_bindings["Move Left"] = pygame.K_a
        mock_load.return_value = new_bindings
        s.reload()
        self.assertEqual(s["Move Left"], pygame.K_a)


if __name__ == "__main__":
    unittest.main()
