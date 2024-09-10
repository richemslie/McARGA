from mcarga.core.baseenum import BaseEnum, auto


class ScoringFunction(BaseEnum):
    BASE = auto()
    DIFF_GRID_SIZES = auto()
    PENALISE_DIFF_ORIG_COLOURS = auto()


class Scoring:
    def __init__(self, config):
        self.config = config

    def __call__(self, anode, in_bundle):
        if self.config.scoring_function == ScoringFunction.BASE:
            fn = self.base

        elif self.config.scoring_function == ScoringFunction.DIFF_GRID_SIZES:
            fn = self.different_size_grids

        elif self.config.scoring_function == ScoringFunction.PENALISE_DIFF_ORIG_COLOURS:
            fn = self.penalise_diff_orig

        else:
            assert False, f"Unsuppoted scoring function {self.config.scoring}"

        return fn(anode, in_bundle)

    def obj_to_hash(self, in_bundle):
        token_strings = []

        if self.config.hashing_include_objects_sigs:
            for ga in in_bundle:
                for obj in ga.objs:
                    token_strings.append(str(obj))
                token_strings.sort()
        return token_strings

    def base(self, anode, in_bundle):
        """
        calculate the total score across all training examples for a given apply call.
        hash the apply call by converting the results to a string and use it as a key to the cache.
        return -1, -1 if the apply call is invalid
        """

        # currently we are just a grid based solve

        score = 0
        token_strings = self.obj_to_hash(in_bundle)

        out_bundle = anode.task_bundle.out_bundle

        for ga, out_graph in zip(in_bundle, out_bundle):
            assert ga.is_training_graph

            # we need out_graph for background_colour below
            bg_colour = out_graph.background_colour

            reconstructed = ga.undo_abstraction()

            num_rows, num_cols = out_graph.shape
            for r in range(num_rows):
                for c in range(num_cols):
                    pixel = reconstructed[r, c]
                    token_strings.append(str(pixel))

                    out_pixel = out_graph.original_grid[r, c]

                    if pixel == out_pixel:
                        continue

                    # else not equal

                    # score based on whether it is background or not
                    if pixel == bg_colour or out_pixel == bg_colour:
                        score += 2
                    else:
                        score += 1

                token_strings.append("<nextrow>")
            token_strings.append("<nextinput>")

        return score, hash("".join(token_strings))

    def different_size_grids(self, anode, in_bundle):
        """
        calculate the total score across all training examples for a given apply call.
        hash the apply call by converting the results to a string and use it as a key to the cache.
        return -1, -1 if the apply call is invalid
        """

        # currently we are just a grid based solve

        out_bundle = anode.task_bundle.out_bundle

        score = 0
        token_strings = self.obj_to_hash(in_bundle)

        for ga, out_graph in zip(in_bundle, out_bundle):
            assert ga.is_training_graph

            # we need out_graph for background_colour below
            bg_colour = out_graph.background_colour

            reconstructed = ga.undo_abstraction()

            in_rows, in_cols = reconstructed.shape
            num_rows, num_cols = out_graph.shape

            solved_grid = in_rows == num_rows and in_cols == num_cols
            for r in range(num_rows):
                # handle case where reconstructed smaller than output
                if r >= in_rows:
                    score += 3 * num_cols
                    solved_grid = False
                    continue

                for c in range(num_cols):

                    # handle case where reconstructed smaller than output
                    if c >= in_cols:
                        score += 3
                        solved_grid = False
                        continue

                    pixel = reconstructed[r, c]
                    token_strings.append(str(pixel))

                    out_pixel = out_graph.original_grid[r, c]

                    if pixel == out_pixel:
                        continue

                    # else not equal
                    solved_grid = False

                    # score based on whether it is background or not
                    if pixel == bg_colour or out_pixel == bg_colour:
                        score += 2
                    else:
                        score += 1

                token_strings.append("<nextrow>")

            token_strings.append("<nextinput>")
            if not solved_grid:
                score += 10

        return score, hash("".join(token_strings))

    def penalise_diff_orig(self, anode, in_bundle):
        DEBUG = False
        score = 0
        token_strings = self.obj_to_hash(in_bundle)

        out_bundle = anode.task_bundle.out_bundle
        orig_in_bundle = anode.task_bundle.in_train_bundle

        for ga, out_ga, orig_ga in zip(in_bundle, out_bundle, orig_in_bundle):
            assert ga.is_training_graph

            bg_colour = ga.background_colour
            reconstructed = ga.undo_abstraction()

            in_rows, in_cols = reconstructed.shape
            num_rows, num_cols = out_ga.shape

            solved_grid = in_rows == num_rows and in_cols == num_cols
            for r in range(num_rows):
                # handle case where reconstructed smaller than output
                if r >= in_rows:
                    score += 3 * num_cols
                    solved_grid = False
                    continue

                for c in range(num_cols):

                    # handle case where reconstructed smaller than output
                    if c >= in_cols:
                        score += 3
                        solved_grid = False
                        continue

                    pixel = reconstructed[r, c]
                    token_strings.append(str(pixel))

                    out_pixel = out_ga.original_grid[r, c]

                    if pixel == out_pixel:
                        continue

                    # else not equal
                    solved_grid = False

                    # else not equal
                    orig_pixel = orig_ga.original_grid[r, c]

                    # this says if we have the same colour as original, fine... but...
                    if pixel == orig_pixel:
                        score += 1.0
                    else:
                        # but if we are getting further off track - small penality
                        score += 1.25

                token_strings.append("<nextrow>")
            token_strings.append("<nextinput>")
            if not solved_grid:
                score += 10

        return score, hash("".join(token_strings))

