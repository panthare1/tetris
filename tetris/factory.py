from logic import ShapeI, ShapeO, ShapeT, ShapeL, ShapeDot
import random

# Fix #8: distinct color per shape type for readability
SHAPE_COLORS = {
    ShapeI:    (0,   220, 220),  # cyan
    ShapeT:    (180, 0,   220),  # purple
    ShapeL:    (220, 140, 0  ),  # orange
    ShapeO:    (220, 220, 0  ),  # yellow
    ShapeDot:  (0,   220, 0  ),  # green
}


class ShapeFactory:
    @staticmethod
    def get_random_shape():
        shape_class = random.choice(list(SHAPE_COLORS))
        return shape_class(3, 0, SHAPE_COLORS[shape_class])