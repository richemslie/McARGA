import time
from dataclasses import dataclass
from typing import Union, Set, Tuple, List

import networkx as nx
import matplotlib.pyplot as plt

from mcarga.statemachine.graph_abstraction import ArcObject, ArcMultiObject


def convert_to_nx(ga):

    g = nx.Graph()
    for node, arc_obj in ga.items():
        if isinstance(arc_obj, ArcObject):
            g.add_node(node, coords=arc_obj.coords, colour=arc_obj.colour, size=arc_obj.size)
        else:
            assert isinstance(arc_obj, ArcMultiObject)
            g.add_node(node, coords=arc_obj.coords, colour=arc_obj.most_common_colour, size=arc_obj.size)

        for edge in arc_obj.edges:
            other, attribute = edge
            # Find the key for 'other' in ga
            other_key = next(key for key, value in ga.items() if value == other)
            g.add_edge(node, other_key, direction=attribute)

    return g


def get_centroid(graph, node):
    """
    get the centroid of a node
    """
    xx = graph.nodes[node]
    center_y = (sum([n[0] for n in xx["coords"]]) + xx["size"] // 2) // xx["size"]
    center_x = (sum([n[1] for n in xx["coords"]]) + xx["size"] // 2) // xx["size"]
    return (center_y, center_x)


def visualise_abstraction(ga, file_name=None):
    """
    visualize the graph
    """

    colours = ["#000000", "#0074D9", "#FF4136", "#2ECC40", "#FFDC00", "#AAAAAA",
               "#F012BE", "#FF851B", "#7FDBFF", "#870C25"]

    graph = convert_to_nx(ga)

    if ga.abstraction_type is None:
        fig = plt.figure(figsize=(6, 6))
    else:
        fig = plt.figure(figsize=(4, 4))

    assert ga.abstraction_type is not None
    pos = {}
    for node in graph.nodes:
        if not isinstance(node, tuple):
            continue
        centroid = get_centroid(graph, node)
        pos[node] = (centroid[1], -centroid[0])

    color = [colours[data["colour"]] for node, data in graph.nodes(data=True)]

    size = [300 * data["size"] for node, data in graph.nodes(data=True)]

    if ga.abstraction_type == "mcccg":
        nx.draw(graph, pos=pos, node_color=color, edgecolors='black', linewidths=2, node_size=size)
    else:
        nx.draw(graph, pos=pos, node_color=color, node_size=size)

    def get_contrasting_color(bg_color):
        # Simple function to return black or white based on background color
        r, g, b = [int(bg_color[i:i+2], 16) for i in (1, 3, 5)]
        return '#000000' if (r * 0.299 + g * 0.587 + b * 0.114) > 186 else '#ffffff'

    for node, (x, y) in pos.items():
        sz = graph.nodes[node]['size']
        node_color = colours[graph.nodes[node]['colour']]
        font_color = get_contrasting_color(node_color)
        plt.text(x, y, str(node),
                 fontsize=9 if sz > 2 else 6,
                 color=font_color,
                 horizontalalignment='center',
                 verticalalignment='center')

    edge_labels = nx.get_edge_attributes(graph, "direction")
    try:
        nx.draw_networkx_edge_labels(graph, pos=pos, edge_labels=edge_labels)
    except Exception:
        print("failed nx.draw_networkx_edge_labels")

    if file_name is not None:
        fig.savefig(file_name)
        plt.close()

    else:
        plt.show()


###############################################################################

def dump(ga, show=False):
    print()
    print(ga.original_grid)
    print(f"background_colour: {ga.background_colour}")
    print()
    print(f"Dumping abstraction : {ga.abstraction_type}")
    for node in sorted(ga.items()):
        print(node)

    if show:
        visualise_abstraction(ga)


###############################################################################

@dataclass
class StoreAttributes:
    " This is/was for testing transformations "
    obj_type: str
    sig_shape: Tuple[Tuple[int, int]]
    bound_box: Tuple[int, int, int, int]
    size: int
    colour: List[int]
    colours: [Set[int]]
    most_common_colour: int
    sig_str: str

    @classmethod
    def from_obj(cls, obj: Union[ArcObject, ArcMultiObject]) -> "StoreAttributes":
        common_attrs = {
            'obj_type': type(obj).__name__,
            'sig_shape': obj.get_signature_shape(),
            'bound_box': obj.bounding_box(),
            'size': obj.size,
            'colour': obj.colour,
            'colours': obj.colours,
            'most_common_colour': obj.most_common_colour,
            'sig_str': repr(obj)
        }
        return StoreAttributes(**common_attrs)

    def assert_all(self, obj: Union[ArcObject, ArcMultiObject], exclude: str = "", ignore: str = "") -> None:
        other = StoreAttributes.from_obj(obj)

        assert self.obj_type == type(obj).__name__

        exclude = set(exclude.split())
        ignore = set(ignore.split())
        for (attr_name, value), other_value in zip(vars(self).items(), vars(other).values()):
            if attr_name in ignore:
                continue

            if attr_name not in exclude:
                other_value = getattr(other, attr_name)
                msg = f"failed == for {attr_name}: expected {value}, got {other_value}"
                assert other_value == value, msg
            else:
                msg = f"failed != for {attr_name}: expected {value}, got {other_value}"
                assert other_value != value, msg

    def diff(self, obj: Union['ArcObject', 'ArcMultiObject']) -> dict:
        other = StoreAttributes.from_obj(obj)
        differences = {}
        for (attr_name, value), other_value in zip(vars(self).items(), vars(other).values()):
            if other_value != value:
                differences[attr_name] = value, other_value

        return differences


###############################################################################

class Timer:
    def __init__(self, description=""):
        self.description = description
        self.start = None
        self.end = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        print(f"{self.description}: {self.end - self.start:.2f}")

    def elapsed(self):
        if self.end is None:
            return time.time() - self.start
        return self.end - self.start
