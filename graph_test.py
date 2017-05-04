import networkx as nx

G = nx.MultiDiGraph()

G.add_node(1)
G.add_node(2)
G.add_node(3)

# Weighted edges:
# SR600: 1.0
# MRR:   5.0

# Add weighted edges for node 1
G.add_weighted_edges_from([(1, 2, 1.0), (1, 2, 5.0), (1, 3, 5.0)])
# Add weighted edges for node 2
G.add_weighted_edges_from([(2, 1, 1.0), (2, 1, 5.0), (2, 3, 1.0), (2, 3, 5.0)])
# Add weighted edges for node 3
G.add_weighted_edges_from([(3, 2, 1.0), (3, 2, 5.0), (3, 1, 5.0)])

print G.nodes()
print G.edges()

# Write grraph to be read by Cytoscape
nx.write_graphml(G, "graph.graphml")
