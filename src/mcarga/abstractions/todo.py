class AbstractionFactory:

    @staticmethod
    def get_largest_rectangle_graph(grid: Grid) -> GraphAbstraction:
        """
        return an abstracted graph where a node is defined as:
        a group of adjacent pixels of the same colour in the original graph that makes up a rectangle, excluding black.
        rectangles are identified from largest to smallest.
        """

        grid = Grid(grid)
        ga = GraphAbstraction(grid, abstraction_type="lrg")
        builder = Builder(ga)

        # https://www.drdobbs.com/database/the-maximal-rectangle-problem/184410529?pgno=1
        def area(llx, lly, urx, ury):
            if llx > urx or lly > ury or [llx, lly, urx, ury] == [0, 0, 0, 0]:
                return 0
            else:
                return (urx - llx + 1) * (ury - lly + 1)

        def all_nb(llx, lly, urx, ury, g):
            for x in range(llx, urx + 1):
                for y in range(lly, ury + 1):
                    if (y, x) not in g:
                        return False
            return True

        lrg = nx.Graph()
        for colour in ga.array_1d:
            if colour == 0:
                continue
            color_nodes = (node for node, data in ga.graph_2d.nodes(data=True) if data.get("color") == colour)
            color_subgraph = ga.graph_2d.subgraph(color_nodes)
            subgraph_nodes = set(color_subgraph.nodes())
            i = 0
            while len(subgraph_nodes) != 0:
                best = [0, 0, 0, 0]
                for llx in range(ga.width):
                    for lly in range(ga.height):
                        for urx in range(ga.width):
                            for ury in range(ga.height):
                                cords = [llx, lly, urx, ury]
                                if area(*cords) > area(*best) and all_nb(*cords, subgraph_nodes):
                                    best = cords
                component = []
                for x in range(best[0], best[2] + 1):
                    for y in range(best[1], best[3] + 1):
                        component.append((y, x))
                        subgraph_nodes.remove((y, x))
                lrg.add_node((color, i), nodes=component, color=color, size=len(component))
                i += 1

        for node_1, node_2 in combinations(lrg.nodes, 2):
            nodes_1 = lrg.nodes[node_1]["nodes"]
            nodes_2 = lrg.nodes[node_2]["nodes"]
            for n1 in nodes_1:
                for n2 in nodes_2:
                    if n1[0] == n2[0]:  # two nodes on the same row
                        for column_index in range(min(n1[1], n2[1]) + 1, max(n1[1], n2[1])):
                            if ga.graph_2d.nodes[n1[0], column_index]["color"] != 0:
                                break
                        else:
                            lrg.add_edge(node_1, node_2, direction=HORIZONTAL)
                            break
                    elif n1[1] == n2[1]:  # two nodes on the same column:
                        for row_index in range(min(n1[0], n2[0]) + 1, max(n1[0], n2[0])):
                            if ga.graph_2d.nodes[row_index, n1[1]]["color"] != 0:
                                break
                        else:
                            lrg.add_edge(node_1, node_2, direction=VERTICAL)
                            break
                else:
                    continue
                break

        return ga
