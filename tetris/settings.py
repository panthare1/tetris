import pygame
import sqlite3
import os

SCREEN_W, SCREEN_H = 300, 600
DB_FILE = os.path.join(os.path.dirname(__file__), "tetris.db")  # ← correct

# Colours (shared with menu.py)
C_BG        = (20,  20,  20)
C_WHITE     = (220, 220, 220)
C_DIM       = (120, 120, 120)
C_ACCENT    = (0,   220, 220)
C_DANGER    = (220, 80,  60)
C_HIGHLIGHT = (40,  40,  40)
C_WAITING   = (220, 180, 0)   # yellow — shown while waiting for a key press

# ── Default bindings ─────────────────────────────────────────────────────────
# Maps action name → default pygame key constant (int)
DEFAULT_BINDINGS: dict[str, int] = {
    "Move Left":  pygame.K_LEFT,
    "Move Right": pygame.K_RIGHT,
    "Soft Drop":  pygame.K_DOWN,
    "Rotate":     pygame.K_UP,
    "Pause":      pygame.K_ESCAPE,
    "Hard Drop":  pygame.K_SPACE,  # ← missing from your file
}


# ── DB helpers ───────────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    # Scores table (kept here so either module can bootstrap the DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            score     INTEGER NOT NULL,
            played_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    # Key bindings table: one row per action
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keybindings (
            action  TEXT PRIMARY KEY,
            keycode INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def load_bindings() -> dict[str, int]:
    """
    Load bindings from the DB, falling back to defaults for any missing action.
    Always returns a complete dict with every action present.
    """
    bindings = dict(DEFAULT_BINDINGS)   # start with defaults
    try:
        with _get_connection() as conn:
            rows = conn.execute("SELECT action, keycode FROM keybindings").fetchall()
            for action, keycode in rows:
                if action in bindings:  # ignore unknown actions from old DB rows
                    bindings[action] = keycode
    except sqlite3.Error:
        pass
    return bindings


def save_bindings(bindings: dict[str, int]) -> None:
    """Upsert all bindings into the DB."""
    try:
        with _get_connection() as conn:
            conn.executemany(
                "INSERT INTO keybindings (action, keycode) VALUES (?, ?)"
                " ON CONFLICT(action) DO UPDATE SET keycode = excluded.keycode",
                bindings.items(),
            )
            conn.commit()
    except sqlite3.Error:
        pass


# ── Settings class ───────────────────────────────────────────────────────────

class Settings:
    """
    Thin wrapper around the bindings dict.
    Import this in main.py and use settings[action] to get the key constant.

    Usage:
        settings = Settings()
        if event.key == settings["Move Left"]:
            ...
    """

    def __init__(self):
        self._bindings = load_bindings()

    def __getitem__(self, action: str) -> int:
        return self._bindings.get(action, DEFAULT_BINDINGS[action])  # ← yours uses [action]

    def reload(self):
        """Re-read bindings from DB (call after SettingsMenu closes)."""
        self._bindings = load_bindings()


# ── SettingsMenu ─────────────────────────────────────────────────────────────

class SettingsMenu:
    """
    Interactive key-rebinding screen.

    show() runs its own event loop and returns "back" when the player is done.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen   = screen
        self.clock    = pygame.time.Clock()
        self.fm       = pygame.font.SysFont(None, 32)
        self.fs       = pygame.font.SysFont(None, 24)
        self.bindings = load_bindings()
        self.actions  = list(DEFAULT_BINDINGS.keys())   # fixed display order

    # ── helpers ──────────────────────────────────────────────────────────────

    def _key_name(self, keycode: int) -> str:
        """Human-readable key name, e.g. 'Left', 'Space', 'A'."""
        name = pygame.key.name(keycode)
        return name.replace("[", "").replace("]", "").title()

    def _is_duplicate(self, action: str, keycode: int) -> bool:
        """Return True if keycode is already used by a *different* action."""
        for a, k in self.bindings.items():
            if a != action and k == keycode:
                return True
        return False

    def _draw(self, selected: int, waiting: bool, conflict: str | None):
        self.screen.fill(C_BG)
        for x in range(0, SCREEN_W, 30):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 30):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (SCREEN_W, y))

        # Title
        title = self.fm.render("KEY BINDINGS", True, C_ACCENT)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_W // 2, centery=40))
        pygame.draw.line(self.screen, C_ACCENT, (30, 62), (SCREEN_W - 30, 62), 1)

        # Each action row
        for i, action in enumerate(self.actions):
            row_y     = 100 + i * 70
            is_sel    = (i == selected)
            is_wait   = is_sel and waiting
            row_color = C_WAITING if is_wait else (C_ACCENT if is_sel else C_WHITE)
            bg_color  = (50, 50, 20) if is_wait else (C_HIGHLIGHT if is_sel else None)

            # Row background
            if bg_color:
                pygame.draw.rect(self.screen, bg_color,
                                 (20, row_y - 10, SCREEN_W - 40, 58), border_radius=8)
            # Highlight border for selected row
            if is_sel:
                border_col = C_WAITING if is_wait else C_ACCENT
                pygame.draw.rect(self.screen, border_col,
                                 (20, row_y - 10, SCREEN_W - 40, 58),
                                 width=1, border_radius=8)

            # Action label
            label = self.fs.render(action, True, C_DIM if not is_sel else row_color)
            self.screen.blit(label, (34, row_y))

            # Key badge
            if is_wait:
                key_text = "press a key…"
            else:
                key_text = self._key_name(self.bindings[action])

            key_surf = self.fm.render(key_text, True, row_color)
            key_rect = key_surf.get_rect(right=SCREEN_W - 34, centery=row_y + 18)
            self.screen.blit(key_surf, key_rect)

        # Conflict warning
        if conflict:
            warn = self.fs.render(f"⚠ already used by {conflict}", True, C_DANGER)
            self.screen.blit(warn, warn.get_rect(centerx=SCREEN_W // 2,
                                                  centery=SCREEN_H - 80))

        # Footer hints
        hints = [
            "^v  navigate",
            "ENTER  rebind selected",
            "R  reset defaults",
            "ESC  back",
        ]
        for j, h in enumerate(hints):
            s = self.fs.render(h, True, C_DIM)
            self.screen.blit(s, s.get_rect(centerx=SCREEN_W // 2,
                                            centery=SCREEN_H - 58 + j * 18))

        pygame.display.flip()

    # ── public ───────────────────────────────────────────────────────────────

    def show(self) -> str:
        """Run the settings screen. Returns 'back' when the player exits."""
        selected = 0
        waiting  = False   # True when we're listening for the next key press
        conflict = None    # name of conflicting action, if any

        while True:
            self._draw(selected, waiting, conflict)
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_bindings(self.bindings)
                    return "back"

                if event.type == pygame.KEYDOWN:
                    conflict = None   # clear any old warning

                    if waiting:
                        # ── capture the new key ──────────────────────────
                        if event.key == pygame.K_ESCAPE:
                            # ESC cancels rebinding without changing anything
                            waiting = False
                        else:
                            action = self.actions[selected]
                            if self._is_duplicate(action, event.key):
                                conflict = next(
                                    a for a, k in self.bindings.items()
                                    if k == event.key and a != action
                                )
                            else:
                                self.bindings[action] = event.key
                                save_bindings(self.bindings)
                            waiting = False
                    else:
                        # ── normal navigation ────────────────────────────
                        if event.key == pygame.K_ESCAPE:
                            save_bindings(self.bindings)
                            return "back"
                        if event.key in (pygame.K_UP, pygame.K_w):
                            selected = (selected - 1) % len(self.actions)
                        if event.key in (pygame.K_DOWN, pygame.K_s):
                            selected = (selected + 1) % len(self.actions)
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            waiting = True
                        if event.key == pygame.K_r:
                            # Reset all bindings to defaults
                            self.bindings = dict(DEFAULT_BINDINGS)
                            save_bindings(self.bindings)