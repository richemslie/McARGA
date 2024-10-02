import random

from mcarga.transformations.transformations import Transformations

from mcarga.statemachine.blackboard import MatchType


###############################################################################

def do_score(ga_in, ga_out):
    from .scoring import simple_scorer_v2
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
    before_score = do_score(ga_in, ga_out)

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

    after_score = do_score(ga_in, ga_out)
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
    before_score = do_score(ga_in, ga_out)

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

    after_score = do_score(ga_in, ga_out)
    print(f"before {before_score}, after: {after_score}")
    print(ga_in.undo_abstraction())
    for t in transformation_list:
        print(t)
    return after_score == 0



