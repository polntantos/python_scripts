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
SELECT ?product ?brand_uri ?product_title ?mpn
WHERE {{
  ?product <http://omikron44/ontologies/products#brand> ?brand_uri ;
           <http://omikron44/ontologies/products#title> ?product_title .
           OPTIONAL{{?product_title <http://omikron44/ontologies/products#mpn> ?mpn}}
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
mpns = [row["mpn"] for row in query_res if "mpn" in row]

vectorizer1 = TfidfVectorizer(
    stop_words="english", ngram_range=(1, 1), min_df=1, max_df=0.5
)  # to catch product sku
vectorizer2 = TfidfVectorizer(
    stop_words="english", ngram_range=(2, 2), min_df=2, max_df=0.5
)
vectorizer3 = TfidfVectorizer(
    stop_words="english", ngram_range=(3, 3), min_df=2, max_df=0.5
)

X1 = vectorizer1.fit_transform(product_titles)
X2 = vectorizer2.fit_transform(product_titles)
X3 = vectorizer3.fit_transform(product_titles)

vocab1 = [
    word for word in vectorizer1.vocabulary_.keys() if brand_name.lower() not in word
]
vocab2 = [
    word for word in vectorizer2.vocabulary_.keys() if brand_name.lower() not in word
]
vocab3 = [
    word for word in vectorizer3.vocabulary_.keys() if brand_name.lower() not in word
]

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

termdict1 = {}
for name1 in vocab1:
    for name2 in vocab2:
        if name1 in name2.split():
            if name1 not in termdict1.keys():
                termdict1[name1] = []
            print(name1, name2)
            termdict1[name1].append(name2)

for ngram, ngrams in termdict1.items():
    if len(G.out_edges(ngram)) == 1:
        for dual in ngrams:
            if dual in vocab2:
                vocab2.pop(vocab2.index(dual))
    elif len(G.out_edges(ngram)) > len(
        [word for word in ngrams if word.startswith(ngram + " ")]
    ):  # Must be a dual word feature filter
        for word in ngrams:
            if word in vocab2:
                print(word)
                vocab2.pop(vocab2.index(word))
        for edge in G.out_edges(ngram):
            value = " ".join(edge)
            if value not in vocab2:
                # print(value)
                vocab2.append(value)
        vocab1.pop(vocab1.index(ngram))
    else:
        vocab1.pop(vocab1.index(ngram))

for word1 in vocab1:
    for word2 in vocab2:
        if word1 in word2.split():
            vocab2.pop(vocab2.index(word2))

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
