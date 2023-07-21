from classes.VirtuosoWrapper import VirtuosoWrapper
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import nltk
from nltk.corpus import stopwords
from rdflib import Graph, URIRef, RDF, RDFS,Literal
import json
from node2vec import Node2Vec
from slugify import slugify
import networkx as nx
from pyvis.network import Network
import math

def create_graph_vis(graph, name="graph_vis", ego=None, distance=1):
    net = Network(
        "1000px", "1900px", directed=True, font_color="white", bgcolor="#111111"
    )
    if ego != None:
        graph = nx.ego_graph(graph, ego, radius=distance, undirected=True)
        name = f"{name}_{ego}"
    net.from_nx(graph)
    net.show(
        f"{name}.html",
        notebook=False,
    )

nltk.download("stopwords")

color_query = """
select ?color_uri ?label
where { 
{?color_uri a <http://magelon.com/ontologies/colors>.}
UNION
{?color_uri a <http://omikron44/ontologies/mixture_colors>.}
UNION
{?color_uri a <http://magelon.com/ontologies/color_variations>.}
?color_uri <http://www.w3.org/2000/01/rdf-schema#label> ?label.
}
"""

brand_name = "Lenovo"
query = f"""
SELECT ?product ?product_title ?mpn ?merchant_id
WHERE {{
  ?product <http://magelon.com/ontologies/products#brand> ?brand_uri ;
           <http://magelon.com/ontologies/products#title> ?product_title .
           ?product <http://magelon.com/ontologies/products#mpn> ?mpn.
           OPTIONAL{{?product <http://magelon.com/ontologies/products#merchant_id> ?merchant_id }}
  {{
    Select ?brand_uri ?brand_name
    WHERE {{
      {{
      ?brand_uri ?p "{brand_name}".
      ?brand_uri <http://magelon.com/ontologies/brands#brand> ?brand_name.
      ?brand_uri a <http://magelon.com/ontologies/brands>.
      }}
      UNION
      {{
      ?b ?n "{brand_name}".
      ?brand_uri ?refers ?b.
      ?brand_uri <http://magelon.com/ontologies/brands#brand> ?brand_name.
      ?brand_uri a <http://magelon.com/ontologies/brands>.
      }}
    }}
  }}
}}
"""

virtuoso = VirtuosoWrapper()
response = virtuoso.getAll(query)
product_titles = [row["product_title"] for row in response]
mpns = set([row["mpn"] for row in response])
response_colors = virtuoso.getAll(color_query)
colors = set([row["label"] for row in response_colors])

G = nx.DiGraph()
for product_title in product_titles:
    # title_parts = re.split(r"\W+", title.lower())
    title= re.sub(r"[>#+'?$%^*®™()]+|-","",product_title)
    title_parts = title.lower().split()
    previous_part=""
    for title_part in title_parts:
        if previous_part !="":
            if(G.has_edge(previous_part,title_part)):
                weight = G[previous_part][title_part]['weight']+1
            else:
                weight = 1
            G.add_edge(previous_part,title_part,weight=weight)
        previous_part = title_part

create_graph_vis(G.copy(),'Lenovo')
most_common_edges = sorted(G.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)[:20]

def get_most_common_paths(G,start,finish):
    paths = []
    try:
        all_shortest_paths = nx.all_shortest_paths(G, start, finish)
        # Score each path using the weight of the edges
        for shortest_path in all_shortest_paths:
            if len(shortest_path) >3:
                continue
            score = 0
            for i in range(len(shortest_path) - 1):
                score += G.edges[shortest_path[i],shortest_path[i+1]]['weight']
            # print(shortest_path, score)
            paths.append(
                {"path":shortest_path,"score":score,"path_score":score/len(shortest_path)}
                )
    except nx.NetworkXNoPath:
        print(f"No path for {start}->{finish}")
    return paths

all_paths = []
for node1 in G.nodes():
    for node2 in G.nodes():
        if node1 != node2:
            all_paths.extend(get_most_common_paths(G,node1,node2))

normal_sorted_paths = sorted(all_paths,key=lambda x:x['score'],reverse=True)

for path in normal_sorted_paths[0:100]:
    print(f"PATH:{' '.join(path['path'])}")
    print(f"SCORE:{path['score']}")
    print(f"FINAL_SCORE:{path['path_score']}\n")

sorted_paths = sorted(all_paths,key=lambda x:x['path_score'],reverse=True)
top_paths_count = math.ceil(len(sorted_paths)/100)*30#top 30%
for path in sorted_paths[0:top_paths_count]:
    print(f"PATH:{' '.join(path['path'])}")
    print(f"SCORE:{path['score']}")
    print(f"FINAL_SCORE:{path['path_score']}\n")

features_in_products = {}
product_features = {}

for product_title in product_titles:
    title= re.sub(r"[>#+'?$%^*®™()]+|-","",product_title)
    title = " ".join(title.lower().split())
    for path in sorted_paths[0:top_paths_count]:
        feature = " ".join(path['path'])
        if feature in title:
            if title not in features_in_products.keys():
                features_in_products[title]=[]
            features_in_products[title].append(feature)
            if slugify(feature) not in product_features.keys():
                product_features[slugify(feature)]= 0
            product_features[slugify(feature)]=product_features[slugify(feature)]+1

for product,features in features_in_products.items():
    print(product)
    print(set(features))

#create them as attributes and throw them in the graph


stopwords_list = stopwords.words("english")
stopwords_list.extend([brand_name, brand_name.lower()])
stopwords_list.extend(map(lambda x: x.lower(), mpns))
stopwords_list.extend(map(lambda x: x.lower(), colors))

json_prods = json.dumps(response)
json_colors = json.dumps(response_colors)

with open("storage/prods.json", "w") as f:
    f.write(json_prods)

with open("storage/colors.json", "w") as f:
    f.write(json_colors)

vectorizer = TfidfVectorizer(
    stop_words=stopwords_list, ngram_range=(1, 2), min_df=1, max_df=0.5
)

X = vectorizer.fit_transform(product_titles)

vocab = [word for word in vectorizer.vocabulary_]

filtered_vocab = []
for word in vocab:
    if word.isdigit() and len(word) <= 3:
        continue
    if word.isalpha() and len(word) <= 2:
        continue
    filtered_vocab.append(word)


# assign colors and mpns to products by checking their titles in rdf.Graph
# sand_words = [word for word in vocab if "sand" in word]

# You now have features to assign to products
# You have named features (brand,color,mpn)
# You have unknown features (
# 'battery 334', '334 year'
# 'plus sanding', 'sanding sh'
# ) etc

# now we need to make a graph out of everything
# assign values as
# ?product <http://magelon.com/ontologies/has_attribute#value_type> <http://magelon.com/ontologies/attribute/value>;
# a <http://magelon.com/ontologies/attribute_type>.
# ?product <http://magelon.com/ontologies/has_attribute#brand> <http://magelon.com/ontologies/attribute/Bosch>;
# a <http://magelon.com/ontologies/brand>.
# maybe we can reason with that (whatever reason is)
# maybe same attribute products show their category by grouping together
# maybe categories find a word to word match in the attributes and help us assign them
product_dict = {}
for row in response:
    transformed_title = row["product_title"].lower()
    product_dict[row["product"]] = {"product_title": row["product_title"]}
    if brand_name.lower() in transformed_title:
        product_dict[row["product"]]["brand"] = brand_name
    if row["mpn"] != "" and row["mpn"].lower() in transformed_title:
        product_dict[row["product"]]["product_number"] = row["mpn"]
    else:
        for mpn in mpns:
            if mpn.lower() in transformed_title:
                product_dict[row["product"]]["product_number"] = mpn
    for color in colors:
        if color.lower() in transformed_title:
            product_dict[row["product"]]["color"] = color
    for feature in filtered_vocab:
        if feature in transformed_title:
            if "features" not in product_dict[row["product"]]:
                product_dict[row["product"]]["features"] = []
            product_dict[row["product"]]["features"].append(feature)

# create rdf graph
graph = Graph()
for product_uri, product_data in product_dict.items():
    if "brand" in product_data.keys():
        graph.add(
            (
                URIRef(product_uri),
                URIRef("http://magelon.com/ontologies/has_attribute#brand"),
                URIRef(
                    base="http://magelon.com/ontologies/attribute/",
                    value=slugify(brand_name),
                ),
            )
        )
    if "product_number" in product_data.keys():
        graph.add(
            (
                URIRef(product_uri),
                URIRef("http://magelon.com/ontologies/has_attribute#product_number"),
                URIRef(
                    base="http://magelon.com/ontologies/attribute/",
                    value=slugify(product_data["product_number"]),
                ),
            )
        )
    if "color" in product_data.keys():
        graph.add(
            (
                URIRef(product_uri),
                URIRef("http://magelon.com/ontologies/has_attribute#color"),
                URIRef(
                    base="http://magelon.com/ontologies/attribute/",
                    value=slugify(product_data["color"]),
                ),
            )
        )
    if "features" in product_data.keys():
        for feature in product_data["features"]:
            graph.add(
                (
                    URIRef(product_uri),
                    URIRef("http://magelon.com/ontologies/has_attribute#uknown"),
                    URIRef(
                        base="http://magelon.com/ontologies/attribute/",
                        value=slugify(feature),
                    ),
                )
            )
            graph.add(
                (
                    URIRef(
                        base="http://magelon.com/ontologies/attribute/",
                        value=slugify(feature),
                    ),
                    RDFS.label,
                    Literal(feature)
                )
            )


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

model.wv.distance("Xiaomi","4g")
# Get the latent representations of the nodes
latent_representations = model.get_embeddings()

# Print the latent representations
print(latent_representations)