import pygame
import sqlite3
import os

SCREEN_W, SCREEN_H = 300, 600
DB_FILE = os.path.join(os.path.dirname(__file__), "tetris.db")

C_BG        = (20,  20,  20)
C_WHITE     = (220, 220, 220)
C_DIM       = (120, 120, 120)
C_ACCENT    = (0,   220, 220)
C_DANGER    = (220, 80,  60)
C_GOLD      = (220, 180, 0)
C_HIGHLIGHT = (40,  40,  40)


def _load_fonts():
    return (
        pygame.font.SysFont(None, 64),
        pygame.font.SysFont(None, 36),
        pygame.font.SysFont(None, 26),
    )


def _blit_centered(surface, rendered, cy):
    rect = rendered.get_rect(centerx=SCREEN_W // 2, centery=cy)
    surface.blit(rendered, rect)


def _draw_button(surface, font, text, cy, selected=False):
    color = C_ACCENT    if selected else C_WHITE
    bg    = C_HIGHLIGHT if selected else None
    label = font.render(text, True, color)
    rect  = label.get_rect(centerx=SCREEN_W // 2, centery=cy)
    if bg:
        pad = 10
        pygame.draw.rect(surface, bg,
                         (rect.x - pad, rect.y - pad // 2,
                          rect.w + pad * 2, rect.h + pad), border_radius=6)
    surface.blit(label, rect)
    return rect


def _get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            score     INTEGER NOT NULL,
            played_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keybindings (
            action  TEXT PRIMARY KEY,
            keycode INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def load_high_score():
    try:
        with _get_connection() as conn:
            row = conn.execute("SELECT MAX(score) FROM scores").fetchone()
            return row[0] if row[0] is not None else 0
    except sqlite3.Error:
        return 0


def save_score(score):
    try:
        with _get_connection() as conn:
            conn.execute("INSERT INTO scores (score) VALUES (?)", (score,))
            conn.commit()
    except sqlite3.Error:
        pass


class MenuManager:

    def __init__(self, screen):
        self.screen     = screen
        self.clock      = pygame.time.Clock()
        self.high_score = load_high_score()
        self.fl, self.fm, self.fs = _load_fonts()

    def _base(self):
        self.screen.fill(C_BG)
        for x in range(0, SCREEN_W, 30):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 30):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (SCREEN_W, y))

    def _record_and_check(self, score):
        is_new_record = score > self.high_score
        save_score(score)
        self.high_score = load_high_score()
        return is_new_record

    def show_start(self):
        selected     = 0
        options      = ["Play", "Settings"]
        button_rects = []
        pygame.event.clear()

        while True:
            self._base()

            title = self.fl.render("TETRIS", True, C_ACCENT)
            _blit_centered(self.screen, title, 140)
            pygame.draw.line(self.screen, C_ACCENT, (60, 173), (SCREEN_W - 60, 173), 2)

            _blit_centered(self.screen,
                           self.fs.render(f"Best: {self.high_score}", True, C_GOLD), 200)

            button_rects = [
                _draw_button(self.screen, self.fm, "Play",     270, selected == 0),
                _draw_button(self.screen, self.fm, "Settings", 320, selected == 1),
            ]

            _blit_centered(self.screen,
                           self.fs.render("Q to quit", True, C_DIM), 370)

            for i, line in enumerate(["<-> : move", "^   : rotate",
                                       "v   : soft drop", "ESC : pause"]):
                _blit_centered(self.screen,
                               self.fs.render(line, True, C_DIM), 440 + i * 26)

            pygame.display.flip()
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEMOTION:
                    for i, rect in enumerate(button_rects):
                        if rect.collidepoint(event.pos):
                            selected = i
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, rect in enumerate(button_rects):
                        if rect.collidepoint(event.pos):
                            return "play" if i == 0 else "settings"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(options)
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(options)
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return "play" if selected == 0 else "settings"
                    if event.key == pygame.K_q:
                        return "quit"

    def show_pause(self, background):
        options      = ["Resume", "Settings", "Quit"]
        selected     = 0
        button_rects = []
        pygame.event.clear()

        while True:
            self.screen.blit(background, (0, 0))

            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            panel_rect = pygame.Rect(40, 160, SCREEN_W - 80, 260)
            pygame.draw.rect(self.screen, (30, 30, 30), panel_rect, border_radius=12)
            pygame.draw.rect(self.screen, C_ACCENT,    panel_rect, width=2, border_radius=12)

            _blit_centered(self.screen, self.fm.render("PAUSED", True, C_ACCENT), 210)

            button_rects = [
                _draw_button(self.screen, self.fm, "Resume",   270, selected == 0),
                _draw_button(self.screen, self.fm, "Settings", 320, selected == 1),
                _draw_button(self.screen, self.fm, "Quit",     370, selected == 2),
            ]

            _blit_centered(self.screen,
                           self.fs.render("^v navigate  ENTER select", True, C_DIM), 410)

            pygame.display.flip()
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEMOTION:
                    for i, rect in enumerate(button_rects):
                        if rect.collidepoint(event.pos):
                            selected = i
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, rect in enumerate(button_rects):
                        if rect.collidepoint(event.pos):
                            return ["resume", "settings", "quit"][i]
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "resume"
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected = (selected - 1) % len(options)
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        selected = (selected + 1) % len(options)
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return ["resume", "settings", "quit"][selected]

    def show_game_over(self, score):
        is_new_record = self._record_and_check(score)
        pygame.event.clear()

        while True:
            self._base()

            _blit_centered(self.screen,
                           self.fm.render("GAME OVER", True, C_DANGER), 150)
            pygame.draw.line(self.screen, C_DANGER, (60, 175), (SCREEN_W - 60, 175), 2)

            _blit_centered(self.screen,
                           self.fm.render(f"Score: {score}", True, C_WHITE), 220)

            if is_new_record:
                _blit_centered(self.screen,
                               self.fm.render("New best!", True, C_GOLD), 265)
            else:
                _blit_centered(self.screen,
                               self.fs.render(f"Best: {self.high_score}", True, C_GOLD), 265)

            _blit_centered(self.screen,
                           self.fm.render("ENTER  retry", True, C_ACCENT), 350)
            _blit_centered(self.screen,
                           self.fs.render("Q  quit", True, C_DIM), 395)

            pygame.display.flip()
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        return "play"
                    if event.key == pygame.K_q:
                        return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return "play"