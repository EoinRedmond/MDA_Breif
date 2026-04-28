import networkx as nx


def build_networkx_graph(graph_data):
    G = nx.DiGraph()

    for node in graph_data["nodes"]:
        G.add_node(
            node["id"],
            type=node["type"],
            evidence=node["evidence"]
        )

    for edge in graph_data["edges"]:
        G.add_edge(
            edge["source"],
            edge["target"],
            relationship=edge["relationship"],
            evidence=edge["evidence"]
        )

    return G