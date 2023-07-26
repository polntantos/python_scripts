import networkx as nx
from node2vec import Node2Vec
import numpy as np

product_dict ={}

nx_graph = nx.DiGraph()
for product_uri, product_data in product_dict.items():
    if "brand" in product_data.keys():
        nx_graph.add_edge(product_data['product_title'], product_data['brand'])
    if "product_number" in product_data.keys():
        nx_graph.add_edge(product_data['product_title'], product_data['product_number'])
    if "color" in product_data.keys():
        nx_graph.add_edge(product_data['product_title'], product_data['color'])
    if "features" in product_data.keys():
        for feature in product_data["features"]:
            nx_graph.add_edge(product_data['product_title'], feature)

print(len(nx_graph.nodes()))
print(len(nx_graph.edges()))

n2v = Node2Vec(graph=nx_graph, dimensions=128, walk_length=100,num_walks=100,workers=4)
model = n2v.fit(window=10,min_count=1,batch_words=4)

# Save embeddings for later use
model.wv.save_word2vec_format("storage/embedings.txt")

# Save model for later use
model.save("storage/embeding_model")

model.wv.distance("lenovo","4gb")
# Get the latent representations of the nodes
latent_representations = model.get_embeddings()

# Print the latent representations
print(latent_representations)