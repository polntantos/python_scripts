from classes.VirtuosoWrapper import VirtuosoWrapper
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import nltk
from nltk.corpus import stopwords
from rdflib import Graph, URIRef, RDF, RDFS
import json
import node2vec
from slugify import slugify
import networkx as nx

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

brand_name = "Bosch"
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


nx_graph = nx.Graph()
for s, p, o in graph.triples((None, None, None)):
    nx_graph.add_edge(s, o)

print(len(nx_graph.nodes()))
print(len(nx_graph.edges()))

model = node2vec.Node2Vec(graph=nx_graph, dimensions=128, walk_length=100)
