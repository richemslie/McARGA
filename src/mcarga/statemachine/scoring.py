

def arga_basic_scorer(in_grid, out_grid, bg_colour):
    ''' was original arga scorer
     you get 2 points a incorrect single pixel that is background
     you get 1 points a incorrect single pixel that is not background
    -- constraint: in_grid.shape == out_grid.shape '''

    assert in_grid.shape == out_grid.shape
    score = 0

    in_rows, in_cols = in_grid.shape
    out_rows, out_cols = out_grid.shape

    for r in range(out_rows):
        for c in range(out_cols):

            in_pixel = in_grid[r, c]
            out_pixel = out_grid[r, c]

            if in_pixel == out_pixel:
                continue

            # score based on whether it is background or not
            if in_pixel == bg_colour or out_pixel == bg_colour:
                score += 2
            else:
                score += 1

    return score


def arga_diff_grid_sizes(in_grid, out_grid, bg_colour):
    """
     small extension to arga_basic_scorer(), add support for multiple grid sizes

     you get 3 points for each pixel that is outside the bounds of the output size
     you get 2 points a incorrect single pixel that is background
     you get 1 points a incorrect single pixel that is not background
      """

    score = 0

    in_rows, in_cols = in_grid.shape
    out_rows, out_cols = out_grid.shape

    for r in range(out_rows):
        # handle case where in_grid smaller than output
        if r >= in_rows:
            score += 3 * out_cols
            continue

        for c in range(out_cols):

            # handle case where in_grid is smaller than output
            if c >= in_cols:
                score += 3
                continue

            in_pixel = in_grid[r, c]
            out_pixel = out_grid[r, c]

            if in_pixel == out_pixel:
                continue

            # score based on whether it is background or not
            if in_pixel == bg_colour or out_pixel == bg_colour:
                score += 2
            else:
                score += 1

        # add in any columns in in_graph not in out_graph
        if in_cols > out_cols:
            score += (out_cols - in_cols) * 3

    # add in any rows in in_graph not in out_graph
    if in_rows > out_rows:
        score += (in_rows - out_rows) * 3 * in_cols

    return score


def cmp_scorer(in_grid, orig_grid, out_grid):
    """
      simple comparing scoring scheme:

     you get 2 points for each pixel that is outside the bounds of the output size
     you get 1.25 points for an incorrect single pixel that is ALSO different from orig
     you get 1 points a incorrect single pixel that is same as orig

     conceptually you get a high penalisation if you stray off the path from the original

     -- NOTE: subjectively, I think this works much better for a pure MCTS search without rollouts

      Extra advantage of this method - does not require background colour
     """

    score = 0

    # restriction for now
    assert in_grid.shape == orig_grid.shape

    in_rows, in_cols = in_grid.shape
    out_rows, out_cols = out_grid.shape

    for r in range(out_rows):
        # handle case where in_grid is smaller than output
        if r >= in_rows:
            score += 2 * out_cols
            continue

        for c in range(out_cols):

            # handle case where in_grid is smaller than output
            if c >= in_cols:
                score += 2
                continue

            in_pixel = in_grid[r, c]
            out_pixel = out_grid[r, c]

            if in_pixel == out_pixel:
                continue

            # else not equal

            orig_pixel = orig_grid[r, c]

            # this says if we have the same colour as original, fine... but...
            if in_pixel == orig_pixel:
                score += 1.0
            else:
                # but if we are getting further off track - small penality
                score += 1.25

        # add in any columns in in_graph not in out_graph
        if in_cols > out_cols:
            score += (out_cols - in_cols) * 2

    # add in any rows in in_graph not in out_graph
    if in_rows > out_rows:
        score += (in_rows - out_rows) * 2 * in_cols

    return score

