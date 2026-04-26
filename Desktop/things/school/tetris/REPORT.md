# Tetris — OOP Coursework Report

## Table of Contents

1. [Introduction](#1-introduction)
2. [Body / Analysis](#2-body--analysis)
   - 2.1 [4 OOP Pillars](#21-4-oop-pillars)
   - 2.2 [Design Pattern — Factory Method](#22-design-pattern--factory-method)
   - 2.3 [Composition and Aggregation](#23-composition-and-aggregation)
   - 2.4 [Reading from File / Writing to File](#24-reading-from-file--writing-to-file)
   - 2.5 [Unit Testing](#25-unit-testing)
   - 2.6 [Code Style](#26-code-style)
3. [Results and Summary](#3-results-and-summary)
   - 3.1 [Results](#31-results)
   - 3.2 [Conclusions](#32-conclusions)
   - 3.3 [Future Extensions](#33-future-extensions)
4. [Resources](#4-resources)

---

## 1. Introduction

### What is this application?

This project is a fully playable **Tetris** game built in Python using the `pygame` library. The classic arcade game is recreated with a graphical interface, keyboard controls, a pause menu, a settings screen for key rebinding, and a persistent high-score system backed by an SQLite database.

The project was chosen from the *Games* category of the coursework topic list and demonstrates all four OOP pillars, the Factory Method design pattern, composition/aggregation, persistent file I/O, and unit testing.

### How to run the program

**Requirements:** Python 3.10+, `pygame`

```bash
pip install pygame
python main.py
```

### How to use the program

| Key (default) | Action |
|---|---|
| `←` / `→` | Move piece left / right |
| `↑` | Rotate piece |
| `↓` | Soft drop |
| `Space` | Hard drop |
| `Esc` | Pause / unpause |

- From the **Start screen** choose *Play* to begin or *Settings* to rebind keys.
- During the game press `Esc` to pause; from the pause menu you can resume, open settings, or quit.
- After game over, press `Enter` to retry or `Q` to quit. Your score is saved automatically.

---

## 2. Body / Analysis

### 2.1 Four OOP Pillars

#### Abstraction

Abstraction hides implementation details behind a clean interface. In this project, `Tetromino` is an **abstract base class** (ABC). It declares `_get_matrices()` as an abstract method, meaning every concrete shape *must* provide its own rotation data, but the rest of the game only interacts with `get_image()` — it never needs to know the internal matrix format.

```python
# logic.py
from abc import ABC, abstractmethod

class Tetromino(ABC):
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.rotation = 0
        self._matrix = self._get_matrices()

    @abstractmethod
    def _get_matrices(self):
        pass

    def get_image(self):
        return self._matrix[self.rotation % len(self._matrix)]
```

The game loop in `main.py` only ever calls `piece.get_image()` — it is completely unaware of how any specific shape stores its rotations.

---

#### Inheritance

Inheritance allows subclasses to reuse and extend the behaviour of a parent class. All seven tetromino types inherit from `Tetromino` and only override `_get_matrices()` to define their unique shapes and rotations:

```python
# logic.py
class ShapeI(Tetromino):
    def _get_matrices(self):
        return [
            [(0, 1), (1, 1), (2, 1), (3, 1)],   # horizontal
            [(2, 0), (2, 1), (2, 2), (2, 3)],   # vertical
        ]

class ShapeT(Tetromino):
    def _get_matrices(self):
        return [
            [(1, 0), (0, 1), (1, 1), (2, 1)],   # up
            [(1, 0), (1, 1), (1, 2), (2, 1)],   # right
            [(0, 1), (1, 1), (2, 1), (1, 2)],   # down
            [(1, 0), (0, 1), (1, 1), (1, 2)],   # left
        ]
```

All shared logic — position tracking (`x`, `y`), rotation index, matrix caching, and `get_image()` — lives once in `Tetromino` and is inherited for free by every subclass.

---

#### Encapsulation

Encapsulation bundles data with the methods that operate on it, and controls access to internal state. Two examples in this project:

**`Board`** owns its `grid` and exposes only three well-defined methods. Nothing outside `Board` reads or writes individual cells directly:

```python
# logic.py
class Board:
    def __init__(self):
        self.width  = 10
        self.height = 20
        self.grid   = [[(0, 0, 0) for _ in range(self.width)]
                        for _ in range(self.height)]

    def is_valid_pos(self, shape, adj_x=0, adj_y=0): ...
    def lock_shape(self, shape): ...
    def clear_lines(self): ...
```

**`Settings`** wraps the bindings dictionary in a private attribute `_bindings`. External code retrieves key constants through `__getitem__` and never modifies the dict directly:

```python
# settings.py
class Settings:
    def __init__(self):
        self._bindings = load_bindings()   # private

    def __getitem__(self, action: str) -> int:
        return self._bindings.get(action, DEFAULT_BINDINGS[action])

    def reload(self):
        self._bindings = load_bindings()
```

---

#### Polymorphism

Polymorphism allows objects of different types to be used through the same interface. The game loop treats every piece identically, calling `get_image()` regardless of whether the piece is a `ShapeI`, `ShapeT`, `ShapeL`, or any other type:

```python
# main.py  (simplified)
for px, py in current_piece.get_image():           # same call for every shape
    pygame.draw.rect(screen, current_piece.color,
                     (round(current_piece.x + px) * 30,
                      round(current_piece.y + py) * 30, 28, 28))
```

`Board.is_valid_pos` and `Board.lock_shape` equally accept any `Tetromino` subclass without modification:

```python
if board.is_valid_pos(current_piece, adj_y=1):   # works for ShapeI, ShapeT, ShapeL …
    current_piece.y += 0.05
else:
    board.lock_shape(current_piece)
```

---

### 2.2 Design Pattern — Factory Method

The **Factory Method** pattern delegates the responsibility of object creation to a dedicated class, keeping the calling code decoupled from concrete types.

`ShapeFactory` is the factory: its static method `get_random_shape()` picks a random shape class, looks up its colour, and constructs the object. `main.py` only calls `ShapeFactory.get_random_shape()` — it never imports or instantiates `ShapeI`, `ShapeT`, etc. directly.

```python
# factory.py
from logic import ShapeI, ShapeO, ShapeT, ShapeL, ShapeDot
import random

SHAPE_COLORS = {
    ShapeI:   (0,   220, 220),
    ShapeT:   (180, 0,   220),
    ShapeL:   (220, 140, 0  ),
    ShapeO:   (220, 220, 0  ),
    ShapeDot: (0,   220, 0  ),
}

class ShapeFactory:
    @staticmethod
    def get_random_shape():
        shape_class = random.choice(list(SHAPE_COLORS))
        return shape_class(3, 0, SHAPE_COLORS[shape_class])
```

**Why Factory Method over other patterns?**

- *Singleton* would be unsuitable — many independent piece instances are needed simultaneously.
- *Builder* is designed for constructing complex objects step-by-step; a tetromino needs no multi-step assembly.
- *Prototype* (clone-based) adds complexity with no benefit here since pieces always start at the same position.
- The **Factory Method** is the most natural fit: it encapsulates which class to instantiate and which colour to assign, and adding a new shape only requires one entry in `SHAPE_COLORS`.

---

### 2.3 Composition and Aggregation

#### Aggregation — `MenuManager` and fonts/clock

`MenuManager` holds references to a `pygame.Surface`, a `pygame.time.Clock`, and font objects. These objects exist independently of `MenuManager` and are passed in or created externally — this is **aggregation** (a "uses-a" relationship):

```python
# menu.py
class MenuManager:
    def __init__(self, screen):
        self.screen = screen          # injected — exists independently
        self.clock  = pygame.time.Clock()
        self.fl, self.fm, self.fs = _load_fonts()
```

#### Composition — `Board` and its grid

`Board` creates and fully owns its `grid`. The grid is a list of lists instantiated inside `__init__` and has no meaning outside the board — this is **composition** (a "owns-a" relationship). When the `Board` is destroyed, its grid ceases to exist:

```python
# logic.py
class Board:
    def __init__(self):
        self.grid = [[(0, 0, 0) for _ in range(self.width)]
                      for _ in range(self.height)]
```

---

### 2.4 Reading from File / Writing to File

The game persists two kinds of data to an **SQLite database** (`tetris.db`):

| Table | Data | When written |
|---|---|---|
| `scores` | Integer score + timestamp | Every game-over |
| `keybindings` | Action name → key code | Every time a key is rebound |

A shared `_get_connection()` helper bootstraps both tables on first run. Scores are saved via `save_score()` and the high score is read with `load_high_score()`. Key bindings are saved with `save_bindings()` and loaded with `load_bindings()`, which falls back to defaults for any missing row.

```python
# menu.py
def save_score(score):
    with _get_connection() as conn:
        conn.execute("INSERT INTO scores (score) VALUES (?)", (score,))
        conn.commit()

def load_high_score():
    with _get_connection() as conn:
        row = conn.execute("SELECT MAX(score) FROM scores").fetchone()
        return row[0] if row[0] is not None else 0
```

```python
# settings.py
def load_bindings() -> dict[str, int]:
    bindings = dict(DEFAULT_BINDINGS)
    with _get_connection() as conn:
        rows = conn.execute("SELECT action, keycode FROM keybindings").fetchall()
        for action, keycode in rows:
            if action in bindings:
                bindings[action] = keycode
    return bindings
```

This approach means scores and key preferences survive across sessions without any manual file management by the user.

---

### 2.5 Unit Testing

Unit tests are written using Python's built-in `unittest` framework in `test_tetris.py`. The test suite contains **42 tests** across 8 test classes, all passing:

```
Ran 42 tests in 0.003s  OK
```

| Test class | Tests | Focus |
|---|---|---|
| `TestBoardInit` | 3 | Grid dimensions and initial state |
| `TestBoardIsValidPos` | 8 | Boundary and collision detection |
| `TestBoardLockShape` | 3 | Pieces written correctly to grid |
| `TestBoardClearLines` | 6 | Line clearing and row shifting |
| `TestShapeI/O/T/L/Dot` | 14 | Rotation counts, cell counts, wrap-around |
| `TestShapeFactory` | 4 | Correct type, valid colour, spawn position |
| `TestSettings` | 5 | Default keys, `__getitem__`, `reload()` |

`unittest.mock.patch` is used to isolate `Settings` from the real database during tests:

```python
@patch("settings.load_bindings", return_value=dict(DEFAULT_BINDINGS))
def test_settings_getitem_returns_keycode(self, _mock):
    s = Settings()
    self.assertEqual(s["Move Left"], DEFAULT_BINDINGS["Move Left"])
```

---

### 2.6 Code Style

The project follows [PEP 8](https://peps.python.org/pep-0008/) guidelines:

- Snake_case for all functions and variables (`get_image`, `clear_lines`, `load_bindings`)
- PascalCase for all classes (`Tetromino`, `ShapeFactory`, `MenuManager`)
- Constants in UPPER_CASE (`DEFAULT_BINDINGS`, `SHAPE_COLORS`, `C_ACCENT`)
- Lines kept under 79 characters
- Logical blank lines between class sections
- Type hints used where appropriate (`dict[str, int]`, `pygame.Surface`)

---

## 3. Results and Summary

### 3.1 Results

- The game is fully playable: pieces spawn, fall, rotate, lock, and lines clear correctly, all verified by 42 unit tests.
- Implementing continuous gravity with a floating-point `y` value (instead of a timer) introduced a subtle truncation bug; switching from `int()` to `round()` in collision detection fixed it.
- The SQLite database proved more robust than a plain text file — it handles concurrent-access edge cases and supports multiple tables (scores and keybindings) in one file.
- The Factory Method pattern made it straightforward to add or remove shape types: only the `SHAPE_COLORS` dictionary needs updating; no other file requires changes.
- Mocking the database layer in unit tests (via `unittest.mock.patch`) was necessary to keep tests fast and side-effect-free, which highlighted the value of keeping I/O isolated in dedicated functions.

### 3.2 Conclusions

This coursework produced a complete, working Tetris implementation that demonstrates all four OOP pillars in a practical context. Abstraction and inheritance allowed the five tetromino types to share all common logic while each defining only its unique shape data. Encapsulation in `Board` and `Settings` kept internal state protected and change-safe. Polymorphism let the game loop handle every piece identically through a single `get_image()` interface. The Factory Method pattern decoupled piece creation from the game loop, and SQLite persistence ensured scores and settings survived across sessions. The 42-test suite gives confidence that the core mechanics are correct.

### 3.3 Future Extensions

- **Next-piece preview** — display the upcoming tetromino in a side panel.
- **Level progression** — increase gravity speed as the score grows.
- **Leaderboard screen** — show the top 10 scores from the `scores` table.
- **Additional shapes** — add `ShapeJ`, `ShapeS`, `ShapeZ` by extending `Tetromino` and adding one entry to `SHAPE_COLORS`.
- **Multiplayer** — a second board rendered side-by-side for two-player local play.

---

## 4. Resources

- [Python `abc` module — Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [pygame documentation](https://www.pygame.org/docs/)
- [Python `unittest` framework](https://docs.python.org/3/library/unittest.html)
- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Refactoring Guru — Factory Method](https://refactoring.guru/design-patterns/factory-method)
- [Python `sqlite3` module](https://docs.python.org/3/library/sqlite3.html)
- [Markdown syntax guide](https://www.markdownguide.org/basic-syntax/)
