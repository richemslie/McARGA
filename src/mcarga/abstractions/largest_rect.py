from mcarga.statemachine.graph_abstraction import GraphAbstraction

class Rectangle:
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def coords(self):
        res = {(x, y) for x in range(self.xmin, self.xmax + 1)
               for y in range(self.ymin, self.ymax + 1)}

        assert len(res)
        assert len(res) == self.area()

        return res

    def area(self):
        return (self.xmax - self.xmin + 1) * (self.ymax - self.ymin + 1)

    def is_true_rectangle(self):
        return (self.xmax - self.xmin > 0) and (self.ymax - self.ymin > 0)

    def __repr__(self):
        return f"Rectangle({self.xmin}, {self.ymin}, {self.xmax}, {self.ymax})"


def find_largest_rectangles(coords, width, height, min_size, allow_lines=False):
    coords_set = set(coords)
    coords = sorted(coords_set)  # Sort coordinates for correct rectangle finding

    rectangles = []
    while coords:
        best = None
        best_area = min_size - 1

        for i, (start_x, start_y) in enumerate(coords):
            for j in range(i, len(coords)):
                x, y = coords[j]
                if x < start_x or y < start_y:
                    continue

                rect = Rectangle(start_x, start_y, x, y)

                # dont allow lines?
                if not allow_lines and not rect.is_true_rectangle():
                    continue

                if rect.area() <= best_area:
                    continue

                if all((cx, cy) in coords_set for cx in range(start_x, x + 1)
                                              for cy in range(start_y, y + 1)):
                    best = rect
                    best_area = rect.area()

        if best is None:
            break

        rectangles.append(best)

        # Remove covered coordinates
        coords = [coord for coord in coords if coord not in best.coords()]
        coords_set -= best.coords()

    return rectangles


def get_colour_coords(grid, colour):
    """Extract coordinates of a specific colour from the grid."""
    return [(i, j) for j, row in enumerate(grid) for i, val in enumerate(row) if val == colour]


def subtract_rectangle_coords(coords, rectangles):
    leftover = set(coords)
    for rect in rectangles:
        leftover -= rect.coords()

    # preserve order
    return [coord for coord in coords if coord in leftover]


def decompose_coords(coords, width, height):
    # first add in any rectangles of size >= 4
    rectangles = find_largest_rectangles(coords, width, height, 4, allow_lines=False)
    coords = subtract_rectangle_coords(coords, rectangles)

    # then add in any rectangles of size >= 2
    lines = find_largest_rectangles(coords, width, height, 2, allow_lines=True)

    # then the remainder is loose pixels, add them
    pixels = subtract_rectangle_coords(coords, lines)

    return rectangles, lines, pixels


def largest_rectangles_graph(ga: GraphAbstraction):
    builder = Builder(ga)

    assert ga.background_colour == 0

    for colour in range(1, 10):
        coords = get_colour_coords(colour)
        rectangles, lines, pixels = decompose_coords(coords, ga.width, ga.height)

        # first add in any rectangles of size >= 4
        for r in rectangles:
            builder.add(colour, r.coords())

        # then add in any rectangles of size >= 2
        for l in lines:
            builder.add(colour, l.coords())

        # then the remainder is loose pixels, add them
        for p in pixels:
            builder.add(colour, [p])

    return builder


def print_rectangles(grid, rectangles):
    for i, rect in enumerate(rectangles):
        print(f"Rectangle {i + 1}: {rect}")
        for y in range(rect.ymin, rect.ymax + 1):
            row = ""
            for x in range(rect.xmin, rect.xmax + 1):
                row += str(grid[y][x]) if grid[y][x] == 1 else "."
            print(row)
        print()


def test_find_largest_rectangles():
    import random
    from pprint import pprint

    test_cases = [
        {
            "name": "Simple grid",
            "grid": [
                [1, 1, 1, 1, 1],
                [1, 1, 1, 0, 1],
                [1, 1, 1, 0, 1],
                [1, 0, 0, 1, 1],
                [1, 0, 0, 1, 1]
            ],
            "colour": 1,
            "min_size": 4
        },
        {
            "name": "Multiple colours",
            "grid": [
                [1, 1, 2, 2, 2],
                [1, 1, 0, 2, 2],
                [3, 3, 3, 0, 2],
                [3, 3, 3, 1, 1],
                [3, 3, 3, 1, 1]
            ],
            "colour": 3,
            "min_size": 3
        },
        {
            "name": "No valid rectangles",
            "grid": [
                [1, 0, 1, 0, 1],
                [0, 1, 0, 1, 0],
                [1, 0, 1, 0, 1],
                [0, 1, 0, 1, 0],
                [1, 0, 1, 0, 1]
            ],
            "colour": 1,
            "min_size": 4
        },
        {
            "name": "Single large rectangle",
            "grid": [
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1]
            ],
            "colour": 1,
            "min_size": 1
        },
        {
            "name": "Complex pattern",
            "grid": [
                [1, 1, 1, 2, 2],
                [1, 1, 0, 2, 2],
                [1, 0, 1, 1, 2],
                [2, 2, 1, 1, 0],
                [2, 2, 0, 0, 1]
            ],
            "colour": 1,
            "min_size": 2
        }
    ]

    for case in test_cases:
        print(f"\nTest case: {case['name']}, colour: {case['colour']}, min_size: {case['min_size']}")
        grid = case['grid']
        colour = case['colour']
        min_size = case['min_size']
        width, height = len(grid[0]), len(grid)

        coords = get_colour_coords(grid, colour)
        random.shuffle(coords)  # Ensure order-independence

        rectangles = find_largest_rectangles(coords, width, height, min_size)
        print(f"Found {len(rectangles)} rectangle(s):")
        print_rectangles(grid, rectangles)

        # Verify non-overlapping
        covered = set()
        for rect in rectangles:
            rect_coords = {(x, y) for x in range(rect.xmin, rect.xmax + 1)
                                  for y in range(rect.ymin, rect.ymax + 1)}
            assert not (covered & rect_coords), "Rectangles overlap!"
            covered |= rect_coords

        # Verify minimum size
        for rect in rectangles:
            assert rect.area() >= min_size, f"Rectangle {rect} is smaller than minimum size {min_size}"


        rects, lines, pixels = decompose_coords(coords, width, height)
        pprint(grid)

        print("rects")
        pprint(rects)
        print("lines")
        pprint(lines)
        print("pixels")
        pprint(pixels)

        print("All checks passed!")
        input()

if __name__ == "__main__":
    test_find_largest_rectangles()
