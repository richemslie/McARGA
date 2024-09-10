import random

from mcarga.transformations.transformations import Transformations

from mcarga.blackboard import MatchType


def simple_scorer(in_grid, out_grid, bg_colour):
    """
     calculate the score - base off Scoring.penalise_diff_orig().
     lower score is better

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


def simple_scorer_v2(in_grid, orig_grid, out_grid):
    """
     calculate the score - base off Scoring.different_size_grids().
     lower score is better

     you get 2 points for each pixel that is outside the bounds of the output size
     you get 1.25 points a incorrect single pixel that is different from orig
     you get 1 points a incorrect single pixel that is same as orig

     conceptually you get a high penalisation if you stray off the path from the original

     -- NOTE: subjectively, I think this works much better for a pure MCTS search without rollouts
     """

    score = 0

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


###############################################################################

def score1(ga_in, ga_out):
    bg = ga_in.background_colour
    reconstructed = ga_in.undo_abstraction()
    return simple_scorer(reconstructed, ga_out.original_grid, bg)


def score2(ga_in, ga_out):
    reconstructed = ga_in.undo_abstraction()
    return simple_scorer_v2(reconstructed, ga_in.original_grid, ga_out.original_grid)


def perform_monte_carlo(mapping, pair, max_rollout_distance=4):
    ga_in, ga_out = pair
    ga_in = ga_in.copy()

    print("mapping", mapping)
    print("perform_monte_carlo in:")
    print(ga_in.undo_abstraction())
    print("perform_monte_carlo out:")
    print(ga_out.undo_abstraction())
    print()
    print()

    # get initial score
    before_score = score2(ga_in, ga_out)

    t = Transformations(ga_in)
    transformation_list = []
    addT = transformation_list.append
    while len(transformation_list) < max_rollout_distance:
        if not mapping:
            break

        key_index = random.choice(list(mapping.keys()))
        list_of_matches = mapping.pop(key_index)

        done = False
        for out_index, match_type in list_of_matches:
            if match_type == MatchType.EXACT:
                done = True
                break

        if done:
            continue

        for out_index, match_type in list_of_matches:
            if match_type == MatchType.SAME_SHAPE_AND_POSITION:
                out_obj = ga_out.get_obj(out_index)
                out_colour = out_obj.colour
                t.update_colour(key_index, out_colour)
                addT(f"TRANSFORMATION update_colour({key_index}, {out_colour})")
                done = True
                break

        if done:
            continue

        for out_index, match_type in list_of_matches:
            if match_type == MatchType.SAME_SHAPE_AND_COLOUR:
                # could try and move it
                print("could try and move it")
                pass
            elif match_type == MatchType.SAME_SHAPE:
                # could try colour it or move it
                if random.random() < 0.5:
                    out_obj = ga_out.get_obj(out_index)
                    out_colour = out_obj.colour
                    t.update_colour(key_index, out_colour)
                    addT(f"TRANSFORMATION update_colour({key_index}, {out_colour})")
                    done = True
                    break
                else:
                    # do some movement
                    pass
            else:
                print("What is this?", match_type)

        if done:
            continue

        # since nothing was done and no exact match - try removing it
        t.remove_object(key_index)
        addT(f"TRANSFORMATION remove({key_index})")

    after_score = score2(ga_in, ga_out)
    print(f"before {before_score}, after: {after_score}")
    print(ga_in.undo_abstraction())
    for t in transformation_list:
        print(t)
    return after_score == 0




def perform_x(mapping, pair, max_rollout_distance=4):
    ga_in, ga_out = pair
    ga_in = ga_in.copy()

    print("mapping", mapping)
    print("perform_x in:")
    print(ga_in.undo_abstraction())
    print("perform_x out:")
    print(ga_out.undo_abstraction())
    print()
    print()

    # get initial score
    before_score = score2(ga_in, ga_out)


    t = Transformations(ga_in)
    transformation_list = []

    # account for all static objects 


    addT = transformation_list.append
    while len(transformation_list) < max_rollout_distance:
        if not mapping:
            break

        key_index = random.choice(list(mapping.keys()))
        list_of_matches = mapping.pop(key_index)

        done = False
        for out_index, match_type in list_of_matches:
            if match_type == MatchType.EXACT:
                done = True
                break

        if done:
            continue

        for out_index, match_type in list_of_matches:
            if match_type == MatchType.SAME_SHAPE_AND_POSITION:
                out_obj = ga_out.get_obj(out_index)
                out_colour = out_obj.colour
                t.update_colour(key_index, out_colour)
                addT(f"TRANSFORMATION update_colour({key_index}, {out_colour})")
                done = True
                break

        if done:
            continue

        for out_index, match_type in list_of_matches:
            if match_type == MatchType.SAME_SHAPE_AND_COLOUR:
                # could try and move it
                print("could try and move it")
                pass
            elif match_type == MatchType.SAME_SHAPE:
                # could try colour it or move it
                if random.random() < 0.5:
                    out_obj = ga_out.get_obj(out_index)
                    out_colour = out_obj.colour
                    t.update_colour(key_index, out_colour)
                    addT(f"TRANSFORMATION update_colour({key_index}, {out_colour})")
                    done = True
                    break
                else:
                    # do some movement
                    pass
            else:
                print("What is this?", match_type)

        if done:
            continue

        # since nothing was done and no exact match - try removing it
        t.remove_object(key_index)
        addT(f"TRANSFORMATION remove({key_index})")

    after_score = score2(ga_in, ga_out)
    print(f"before {before_score}, after: {after_score}")
    print(ga_in.undo_abstraction())
    for t in transformation_list:
        print(t)
    return after_score == 0



