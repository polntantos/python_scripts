import re
import networkx as nx
from pyvis.network import Network
from classes.VirtuosoWrapper import VirtuosoWrapper
from sklearn.feature_extraction.text import TfidfVectorizer


def create_graph_vis(graph, name="brand_word_network", ego=None, distance=1):
    net = Network(
        "1000px",
        "1900px",
        directed=True,
        font_color="white",
        bgcolor="#111111",
        neighborhood_highlight=True,
    )
    if ego != None:
        graph = nx.ego_graph(graph, ego, radius=distance, undirected=True)
        name = f"{name}_{ego}"
    net.from_nx(graph, edge_weight_transf=(lambda x: 2 * x), show_edge_weights=True)
    net.show(
        f"{name}.html",
        notebook=False,
    )


# query = """
# SELECT ?title
# WHERE {
#   ?s ?p <http://omikron44/ontologies/brands/id=1696>.
#   ?s a <http://omikron44/ontologies/products>.
#   ?s <http://omikron44/ontologies/products#title> ?title.
# }
# """

brand_name = "Bosch"
query = f"""
SELECT ?product ?brand_uri ?product_title
WHERE {{
  ?product <http://omikron44/ontologies/products#brand> ?brand_uri ;
           <http://omikron44/ontologies/products#title> ?product_title .
  {{
    Select ?brand_uri ?brand_name
    WHERE {{
      {{
      ?brand_uri ?p "{brand_name}".
      ?brand_uri <http://omikron44/ontologies/brands#brand> ?brand_name.
      ?brand_uri a <http://omikron44/ontologies/brands>.
      }}
      UNION
      {{
      ?b ?n "{brand_name}".
      ?brand_uri ?refers ?b.
      ?brand_uri <http://omikron44/ontologies/brands#brand> ?brand_name.
      ?brand_uri a <http://omikron44/ontologies/brands>.
      }}
    }}
  }}
}}
"""

virtuoso = VirtuosoWrapper()
query_res = virtuoso.getAll(query)
product_titles = [row["product_title"] for row in query_res]

G = nx.DiGraph()

transformed_titles = []

for product_title in product_titles:
    words = re.split(r"\W+", product_title.lower())
    transformed_titles.append("_".join(words))
    previous_word = ""
    for word in words:
        if word != "" and word != previous_word:
            # G.add_edge(product_title.lower(), word.lower())
            if previous_word != "":
                if G.has_edge(previous_word, word):
                    weight = G.edges[previous_word, word]["weight"]
                    weight += 1
                    G.add_edge(previous_word, word, weight=weight + 1)
                else:
                    G.add_edge(previous_word, word, weight=1)
            previous_word = word

# create_graph_vis(G, "bosch_attr_brand_word_network") # uncomment this for visual graph (small graph only)

# for degree, in_degree, out_degree in zip(G.degree(), G.in_degree(), G.out_degree()):
#     print(degree, in_degree[1], out_degree[1])

# suspected_values = []
# feature_values = []
# for node, degree in G.degree():
#     if degree % 2 == 1:
#         suspected_values.append(node)
#         # print(node)
#     else:
#         feature_values.append(node)

# possible_features = []
# for node1 in suspected_values:
#     previous_node = None
#     string_val = ""
#     for node2 in suspected_values:
#         if G.has_edge(node1, node2):
#             previous_node = node2
#             string_val = node2
#             possible_features.append("_".join([node1, node2]))
#         elif G.has_edge(previous_node, node2):
#             string_val = "_".join([string_val, node2])
#             possible_features.append(string_val)
#         else:
#             previous_node = None
#             string_val = ""

# for value in possible_features:
#     if "lawnmower" in value:
#         print(value)

sorted_word_pairs = sorted(G.edges(data="weight"), key=lambda x: x[2], reverse=True)

# Collecting numbers of weights
word_connection_weights = set([word_pair[2] for word_pair in sorted_word_pairs])

average = sum(word_connection_weights) / len(word_connection_weights)

possible_feature_paths = []
for pair1 in sorted_word_pairs:
    if pair1[2] > average:
        possible_feature_paths.append("_".join([pair1[0], pair1[1]]))
        for pair2 in sorted_word_pairs:
            if G.has_edge(pair1[1], pair2[0]):
                possible_feature = "_".join([pair1[0], pair1[1], pair2[0]])
                possible_feature_paths.append(possible_feature)
            if G.has_edge(pair2[1], pair1[0]):
                possible_feature = "_".join([pair2[1], pair1[0], pair1[1]])
                possible_feature_paths.append(possible_feature)

# for possible_feature in possible_feature_paths:

vectorizer = TfidfVectorizer(
    stop_words="english", ngram_range=(1, 2), min_df=10, max_df=0.5
)

vectorizer.fit(product_titles)

tf_idf_vectors = vectorizer.transform(product_titles)

# Print the TF-IDF vectors
print(tf_idf_vectors)
input("Press any key to continue...")

vocab = vectorizer.vocabulary_
vocab = sorted(vocab.items(), key=lambda x: x[1], reverse=True)

feature_values = [i[0] for i in vocab]

# must check possible paths of features in graph to see word occurence
features_removed = []
for value, seen in vocab:
    for value2, seen in vocab:
        if value2 != value and value2 in value:
            if value2 in feature_values:
                features_removed.append(
                    feature_values.pop(feature_values.index(value2))
                )


print(possible_features)
print(suspected_values)
