transformation_ops = {"default": ["remove_object", "update_colour", "move_object",
                                  "move_object_max", "extend_object",
                                  "add_border_around_object", "mirror_object", "rotate_object",
                                  "hollow_rectangle", "fill_rectangle", "reflect_axis"],

                      "default_dg": ["remove_object", "update_colour", "move_object",
                                     "move_object_max",  "mirror_object", "rotate_object",
                                     "hollow_rectangle", "fill_rectangle", "reflect_axis"],

                      "scg": ["remove_object", "update_colour"],
                      "lrg": ["remove_object", "update_colour", "add_border_around_object", "hollow_rectangle"],

                      "vcg_nb": ["remove_object", "update_colour", "move_object",
                                 "extend_object", "move_object_max"],

                      "hcg_nb": ["remove_object", "update_colour", "move_object",
                                 "extend_object", "move_object_max"],

                      "mcg_nb": ["remove_object", "mirror_object", "rotate_object", "fill_rectangle"],
                      "na": ["mirror_object", "rotate_object", "fill_rectangle"], }


def get_ops(abstraction):
    if abstraction in transformation_ops:
        return transformation_ops[abstraction]
    else:
        if abstraction.endswith("dg"):
            return transformation_ops["default_dg"]
        else:
            return transformation_ops["default"]
