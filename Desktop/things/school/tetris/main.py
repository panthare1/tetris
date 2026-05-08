import pygame
from factory import ShapeFactory
from logic import Board
from menu import MenuManager
from settings import Settings, SettingsMenu


def reset_game():
    board = Board()
    piece = ShapeFactory.get_random_shape()
    return board, piece, 0


class Game:
    def __init__(self, screen):
        self.screen   = screen
        self.clock    = pygame.time.Clock()
        self.menus    = MenuManager(screen)
        self.settings = Settings()
        self.font     = pygame.font.SysFont(None, 28)

        self.state         = "start"
        self.game_snapshot = None
        self.board, self.current_piece, self.score = reset_game()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _lock_and_spawn(self):
        """Lock the current piece, clear lines, spawn next. Returns False on game over."""
        self.board.lock_shape(self.current_piece)
        lines = self.board.clear_lines()
        self.score += lines * 100
        self.current_piece = ShapeFactory.get_random_shape()
        if not self.board.is_valid_pos(self.current_piece):
            self.state = "game_over"
            return False
        return True

    # ── update ───────────────────────────────────────────────────────────────

    def _update(self):
        """Apply gravity. Lock piece if it can't fall further."""
        if self.board.is_valid_pos(self.current_piece, adj_y=1):
            self.current_piece.y += 0.05
        else:
            self._lock_and_spawn()

    # ── input ────────────────────────────────────────────────────────────────

    def _handle_input(self):
        """Process all pygame events for the playing state."""
        s = self.settings   # shorthand

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = "quit"
                return

            if event.type != pygame.KEYDOWN:
                continue

            key = event.key

            if key == s["Pause"]:
                self.game_snapshot = self.screen.copy()
                self.state = "paused"

            elif key == s["Move Left"]:
                if self.board.is_valid_pos(self.current_piece, adj_x=-1):
                    self.current_piece.x -= 1

            elif key == s["Move Right"]:
                if self.board.is_valid_pos(self.current_piece, adj_x=1):
                    self.current_piece.x += 1

            elif key == s["Soft Drop"]:
                if self.board.is_valid_pos(self.current_piece, adj_y=1):
                    self.current_piece.y += 1

            elif key == s["Hard Drop"]:
                while self.board.is_valid_pos(self.current_piece, adj_y=1):
                    self.current_piece.y += 1
                self._lock_and_spawn()
                return   # skip further events this frame

            elif key == s["Rotate"]:
                self._try_rotate()

    def _try_rotate(self):
        """Rotate with simple wall-kick: try centre, then nudge right, then left."""
        piece = self.current_piece
        piece.rotation += 1
        for nudge in (0, 1, -2):          # 0 = no nudge, +1 right, -1 left
            piece.x += nudge
            if self.board.is_valid_pos(piece):
                return
        # All attempts failed — revert
        piece.x += 1                      # undo the last nudge (-2 + 1 = -1 net, so +1 restores)
        piece.rotation -= 1

    # ── draw ─────────────────────────────────────────────────────────────────

    def _draw(self):
        """Render the board, current piece, and score."""
        self.screen.fill((20, 20, 20))

        # Locked cells
        for y, row in enumerate(self.board.grid):
            for x, color in enumerate(row):
                if color != (0, 0, 0):
                    pygame.draw.rect(self.screen, color, (x * 30, y * 30, 28, 28))

        # Falling piece
        for px, py in self.current_piece.get_image():
            pygame.draw.rect(
                self.screen, self.current_piece.color,
                (round(self.current_piece.x + px) * 30,
                 round(self.current_piece.y + py) * 30, 28, 28)
            )

        # HUD
        self.screen.blit(
            self.font.render(f"Score: {self.score}", True, (200, 200, 200)),
            (8, 8)
        )
        pygame.display.flip()

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:

            if self.state == "start":
                action = self.menus.show_start()
                if action == "quit":
                    break
                if action == "settings":
                    SettingsMenu(self.screen).show()
                    self.settings.reload()
                    continue
                self.board, self.current_piece, self.score = reset_game()
                self.state = "playing"

            elif self.state == "game_over":
                action = self.menus.show_game_over(self.score)
                if action == "quit":
                    break
                self.board, self.current_piece, self.score = reset_game()
                self.state = "playing"

            elif self.state == "paused":
                action = self.menus.show_pause(self.game_snapshot)
                if action == "quit":
                    break
                if action == "settings":
                    SettingsMenu(self.screen).show()
                    self.settings.reload()
                    continue
                self.state = "playing"

            elif self.state == "playing":
                self._update()
                self._handle_input()
                if self.state == "playing":
                    self._draw()
                self.clock.tick(60)

            elif self.state == "quit":
                break


def main():
    pygame.init()
    screen = pygame.display.set_mode((300, 600))
    pygame.display.set_caption("Tetris")
    Game(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()