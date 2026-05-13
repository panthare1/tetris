import pygame
from factory import ShapeFactory
from logic import Board, LINE_SCORES
from menu import MenuManager
from settings import Settings, SettingsMenu


def reset_game():
    board = Board()
    piece = ShapeFactory.get_random_shape()
    return board, piece, 0, 1  # board, piece, score, level


def main():
    pygame.init()
    screen = pygame.display.set_mode((300, 600))
    pygame.display.set_caption("Tetris")
    clock    = pygame.time.Clock()
    menus    = MenuManager(screen)
    settings = Settings()
    font     = pygame.font.SysFont(None, 28)

    state         = "start"
    game_snapshot = None
    board, current_piece, score, level = reset_game()

    while True:

        # ── start screen ─────────────────────────────────────────────────────
        if state == "start":
            action = menus.show_start()
            if action == "quit":
                break
            if action == "settings":
                SettingsMenu(screen).show()
                settings.reload()
                continue
            board, current_piece, score, level = reset_game()
            state = "playing"
            continue

        # ── game over screen ──────────────────────────────────────────────────
        if state == "game_over":
            action = menus.show_game_over(score)
            if action == "quit":
                break
            board, current_piece, score, level = reset_game()
            state = "playing"
            continue

        # ── pause screen ──────────────────────────────────────────────────────
        if state == "paused":
            action = menus.show_pause(game_snapshot)
            if action == "quit":
                break
            if action == "settings":
                SettingsMenu(screen).show()
                settings.reload()
                state = "paused"
                continue
            state = "playing"
            continue

        # ── playing ───────────────────────────────────────────────────────────
        screen.fill((20, 20, 20))

        # 1. GRAVITY
        if board.is_valid_pos(current_piece, adj_y=1):
            current_piece.y += 0.05 + (level - 1) * 0.02
        else:
            board.lock_shape(current_piece)
            lines = board.clear_lines()
            score += LINE_SCORES.get(lines, 0)
            level = score // 500 + 1  # level up every 500 points
            current_piece = ShapeFactory.get_random_shape()
            if not board.is_valid_pos(current_piece):
                state = "game_over"
                continue

        # 2. INPUT
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == settings["Pause"]:
                    game_snapshot = screen.copy()  # capture frame before pausing
                    state = "paused"

                elif event.key == settings["Soft Drop"]:
                    if board.is_valid_pos(current_piece, adj_y=1):
                        current_piece.y += 1

                elif event.key == settings["Move Left"]:
                    if board.is_valid_pos(current_piece, adj_x=-1):
                        current_piece.x -= 1

                elif event.key == settings["Move Right"]:
                    if board.is_valid_pos(current_piece, adj_x=1):
                        current_piece.x += 1

                elif event.key == settings["Hard Drop"]:
                    while board.is_valid_pos(current_piece, adj_y=1):
                        current_piece.y += 1
                    board.lock_shape(current_piece)
                    lines = board.clear_lines()
                    score += LINE_SCORES.get(lines, 0)
                    level = score // 500 + 1
                    current_piece = ShapeFactory.get_random_shape()
                    if not board.is_valid_pos(current_piece):
                        state = "game_over"
                    break

                elif event.key == settings["Rotate"]:
                    current_piece.rotation += 1
                    if not board.is_valid_pos(current_piece):
                        current_piece.x += 1
                        if not board.is_valid_pos(current_piece):
                            current_piece.x -= 2
                            if not board.is_valid_pos(current_piece):
                                current_piece.x += 1
                                current_piece.rotation -= 1

        if state != "playing":
            continue

        # 3. DRAW
        for y, row in enumerate(board.grid):
            for x, color in enumerate(row):
                if color != (0, 0, 0):
                    pygame.draw.rect(screen, color, (x * 30, y * 30, 28, 28))

        for px, py in current_piece.get_image():
            pygame.draw.rect(
                screen, current_piece.color,
                (round(current_piece.x + px) * 30,
                 round(current_piece.y + py) * 30, 28, 28)
            )

        screen.blit(font.render(f"Score: {score}", True, (200, 200, 200)), (8, 8))
        screen.blit(font.render(f"Level: {level}", True, (200, 200, 200)), (8, 28))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()