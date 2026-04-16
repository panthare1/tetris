import pygame
from factory import ShapeFactory
from logic import Board
from menu import MenuManager
from settings import Settings, SettingsMenu


# Board and screen sizing
CELL_SIZE = 30
CELL_INSET = 2
BOARD_PX_W = 10 * CELL_SIZE
BOARD_PX_H = 20 * CELL_SIZE
SCREEN_W = BOARD_PX_W
SCREEN_H = BOARD_PX_H

# Background styling
GRADIENT_BASE = 18
GRADIENT_RANGE = 24
GRADIENT_BLUE_TINT = 4
GRID_LINE_COLOR = (40, 40, 44)

# Block styling
BLOCK_BORDER_RADIUS = 5
BLOCK_BORDER_LIGHTEN = 45
BLOCK_HIGHLIGHT = 70
BLOCK_SHADOW = -70
BLOCK_LINE_WIDTH = 2

# Frame styling
FRAME_COLOR = (16, 16, 18)
FRAME_WIDTH = 4
FRAME_RADIUS = 4


def _shade(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color)


def draw_background(screen):
    gradient_step = GRADIENT_RANGE / SCREEN_H
    for y in range(SCREEN_H):
        v = GRADIENT_BASE + int(y * gradient_step)
        pygame.draw.line(screen, (v, v, v + GRADIENT_BLUE_TINT), (0, y), (SCREEN_W, y))

    for x in range(0, BOARD_PX_W, CELL_SIZE):
        pygame.draw.line(screen, GRID_LINE_COLOR, (x, 0), (x, BOARD_PX_H))
    for y in range(0, BOARD_PX_H, CELL_SIZE):
        pygame.draw.line(screen, GRID_LINE_COLOR, (0, y), (BOARD_PX_W, y))


def draw_block(screen, grid_x, grid_y, color):
    x = grid_x * CELL_SIZE + CELL_INSET
    y = grid_y * CELL_SIZE + CELL_INSET
    size = CELL_SIZE - (CELL_INSET * 2)
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, color, rect, border_radius=BLOCK_BORDER_RADIUS)
    pygame.draw.rect(screen, _shade(color, BLOCK_BORDER_LIGHTEN), rect, width=BLOCK_LINE_WIDTH, border_radius=BLOCK_BORDER_RADIUS)
    pygame.draw.line(
        screen, _shade(color, BLOCK_HIGHLIGHT),
        (rect.left + CELL_INSET, rect.top + CELL_INSET),
        (rect.right - CELL_INSET, rect.top + CELL_INSET),
        BLOCK_LINE_WIDTH,
    )
    pygame.draw.line(
        screen, _shade(color, BLOCK_SHADOW),
        (rect.left + CELL_INSET, rect.bottom - CELL_INSET),
        (rect.right - CELL_INSET, rect.bottom - CELL_INSET),
        BLOCK_LINE_WIDTH,
    )


def draw_board_frame(screen):
    frame = pygame.Rect(0, 0, BOARD_PX_W, BOARD_PX_H)
    pygame.draw.rect(screen, FRAME_COLOR, frame, width=FRAME_WIDTH, border_radius=FRAME_RADIUS)


def reset_game():
    board = Board()
    piece = ShapeFactory.get_random_shape()
    return board, piece, 0


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    menus = MenuManager(screen)
    settings = Settings()
    font     = pygame.font.SysFont(None, 28)

    state         = "start"
    game_snapshot = None
    board, current_piece, score = reset_game()

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
            board, current_piece, score = reset_game()
            state = "playing"
            continue

        # ── game over screen ──────────────────────────────────────────────────
        if state == "game_over":
            action = menus.show_game_over(score)
            if action == "quit":
                break
            board, current_piece, score = reset_game()
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
        draw_background(screen)

        # 1. GRAVITY
        if board.is_valid_pos(current_piece, adj_y=1):
            current_piece.y += 0.05
        else:
            board.lock_shape(current_piece)
            lines = board.clear_lines()
            score += lines * 100
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
                    score += lines * 100
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
                    draw_block(screen, x, y, color)

        for px, py in current_piece.get_image():
            draw_block(
                screen,
                round(current_piece.x + px),
                round(current_piece.y + py),
                current_piece.color,
            )

        draw_board_frame(screen)
        screen.blit(font.render(f"Score: {score}", True, (200, 200, 200)), (8, 8))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
