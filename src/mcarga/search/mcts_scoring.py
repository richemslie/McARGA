from mcarga.core.baseenum import BaseEnum, auto

from mcarga.statemachine.scoring import arga_basic_scorer, arga_diff_grid_sizes, cmp_scorer


class ScoringFunction(BaseEnum):
    ORIGINAL_ARGA = auto()
    DIFF_GRID_SIZES = auto()
    PENALISE_DIFF_ORIG_COLOURS = auto()


class Scoring:
    def __init__(self, config):
        self.config = config

    def __call__(self, anode, in_bundle):
        fn_mapping = {
            ScoringFunction.ORIGINAL_ARGA: self.original_arga,
            ScoringFunction.DIFF_GRID_SIZES: self.different_size_grids,
            ScoringFunction.PENALISE_DIFF_ORIG_COLOURS: self.penalise_diff_orig
            }

        fn = fn_mapping[self.config.scoring_function]
        score = fn(anode, in_bundle)
        hash_val = self.hash_bundle(in_bundle)
        return score, hash_val

    def hash_bundle(self, in_bundle):
        token_strings = []

        if self.config.hashing_include_objects_sigs:
            for ga in in_bundle:
                for obj in ga.objs:
                    token_strings.append(str(obj))
            token_strings.sort()

        for ga in in_bundle:
            reconstructed = ga.undo_abstraction()

            num_rows, num_cols = ga.shape
            for r in range(num_rows):
                for c in range(num_cols):
                    pixel = reconstructed[r, c]
                    token_strings.append(str(pixel))

                token_strings.append("<nextrow>")
            token_strings.append("<nextinput>")

        return hash("".join(token_strings))

    def original_arga(self, anode, in_bundle):
        out_bundle = anode.task_bundle.out_bundle

        total_score = 0
        for ga, out_graph in zip(in_bundle, out_bundle):
            assert ga.is_training_graph

            bg_colour = out_graph.background_colour
            reconstructed = ga.undo_abstraction()

            total_score += arga_basic_scorer(reconstructed, out_graph.original_grid, bg_colour)

        return total_score

    def different_size_grids(self, anode, in_bundle):
        """
        calculate the total score across all training examples for a given apply call.
        """

        out_bundle = anode.task_bundle.out_bundle

        total_score = 0
        for ga, out_graph in zip(in_bundle, out_bundle):
            assert ga.is_training_graph

            bg_colour = out_graph.background_colour
            reconstructed = ga.undo_abstraction()

            score = arga_diff_grid_sizes(reconstructed, out_graph.original_grid, bg_colour)

            total_score += score

        return total_score

    def penalise_diff_orig(self, anode, in_bundle):
        out_bundle = anode.task_bundle.out_bundle
        orig_in_bundle = anode.task_bundle.in_train_bundle

        total_score = 0
        for ga, out_ga, orig_ga in zip(in_bundle, out_bundle, orig_in_bundle):
            assert ga.is_training_graph

            reconstructed = ga.undo_abstraction()

            score = cmp_scorer(reconstructed, orig_ga.original_grid, out_ga.original_grid)

            # here we add an extra penality for each unsolved training example
            if score != 0:
                score += 10

            total_score += score

        return total_score

