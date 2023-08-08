from classes.VirtuosoWrapper import VirtuosoWrapper
import re
import json
import nltk
from nltk.corpus import stopwords
import copy
import networkx as nx
import pandas as pd
from classes.VirtuosoWrapper import VirtuosoWrapper
import matplotlib.pyplot as plt
from pyvis.network import Network
from rdflib import Graph, URIRef, RDF, Literal

nltk.download("stopwords")


def is_stopword(word):
    stopword_set = set(stopwords.words("english"))  # Get the set of English stopwords
    return word.lower() in stopword_set


def evaluate_string(string):
    score = 0
    if "'" in string:
        score += 2
    symbol_count = sum(1 for char in string if char.isalpha())
    symbol_count += sum(2 for char in string if char.isspace())
    score += symbol_count
    if "-" in string:
        score += 2
    words = string.split(" ")
    for word in words:
        if "." in word and len(word.split(".")) > 2:
            score += 2
    if ":" in string and len(string.split(":")) > 2:
        score += 2
    return score


virtuoso = VirtuosoWrapper()

brands_query = """
    SELECT ?brand_uri ?name
    WHERE {
        ?brand_uri a <http://magelon.com/ontologies/brands> .
        ?brand_uri <http://magelon.com/ontologies/brands#brand> ?name .
    }"""

brands = virtuoso.getAll(brands_query)

brands_to_remove = []

for brand in brands:
    if re.search(r"[>/#?$%^*®™()]+", brand["name"]):
        brands_to_remove.append(brand)
    elif len(brand["name"]) > 70:
        brands_to_remove.append(brand)

# Remove values with symbols
brands = [
    brand for brand in brands if not re.search(r"[>/#?$%!^*®™()]+", brand["name"])
]
brands = [brand for brand in brands if not len(brand["name"]) > 70]


transformed_array = [
    re.sub(r"[^a-z0-9]+", "", brand["name"].lower())
    for brand in brands
    if not re.search(r"[>/#?$%^&*()]+", brand["name"])
]

duplicates = {}
for value in brands:
    term = re.sub(r"[^a-zA-Z]+", "", value["name"].lower())
    if transformed_array.count(term) > 1:
        if term not in duplicates:
            duplicates[term] = []
        duplicates[term].append(value)


duplicate_remains = []
# turn to rule based selection of duplicates
for dupli_name, duplicate_array in duplicates.items():
    brand_scores = {}
    for index, duplicate_brand in enumerate(duplicate_array):
        term_score = evaluate_string(duplicate_brand["name"])
        print(f"{index} : {term_score} : {duplicate_brand['name']}")
        brand_scores[index] = term_score
    max_key = max(brand_scores, key=lambda k: brand_scores[k])
    print(f"selected key {max_key}")
    duplicate_remains.append(duplicate_array[int(max_key)])

print(duplicate_remains)
with open("duplicate_remains.json", "w") as dr:
    json.dump(duplicate_remains, dr)

with open("duplicate_remains.json", "r") as dr:
    duplicate_remains = json.load(dr)

duplicate_invalidates = []
for dupli_name, duplicate_array in duplicates.items():
    for index, duplicate_brand in enumerate(duplicate_array):
        if duplicate_brand not in duplicate_remains:
            print(duplicate_brand)
            duplicate_invalidates.append(duplicate_brand)

print(duplicate_invalidates)
with open("duplicate_invalidates.json", "w") as dr:
    json.dump(duplicate_invalidates, dr)

with open("duplicate_invalidates.json", "r") as dr:
    duplicate_invalidates = json.load(dr)

# Remove duplicates
for duplicate_invalidate in duplicate_invalidates:
    if duplicate_invalidate in brands:
        brands_to_remove.append(brands.pop(brands.index(duplicate_invalidate)))


result_dict = {}
# check if valid brands are contained in other brands
for i, value in enumerate(brands):
    print(f"current key {i}")
    contained_values = []
    for j, other_value in enumerate(brands):
        if (
            i != j
            and value["name"].lower() in other_value["name"].lower()
            and value["name"] != ""
            and not is_stopword(value["name"])
        ):
            if len(other_value["name"].split()) > 1 and len(value["name"].split()) == 1:
                if value["name"].lower() in other_value["name"].lower().split():
                    contained_values.append(other_value)
            elif len(other_value["name"].split()) == 1 and len(value["name"].split()) == 1:
                if value["name"].lower() == other_value["name"].lower():
                    contained_values.append(other_value)
            else:
                contained_values.append(other_value)
    print(contained_values)
    if len(contained_values) > 0:
        result_dict[value["name"]] = {}
        result_dict[value["name"]]["main"] = value
        result_dict[value["name"]]["contained"] = contained_values

with open("result_dict.json", "w") as dr:
    json.dump(result_dict, dr)

with open("result_dict.json", "r") as dr:
    result_dict = json.load(dr)

# Ακόμα δεν έχουμε δεδομένα παρουσίας τίτλων brand μεσα στη βάση από ανάλυση τίτλων επομένως θα θεωρήσουμε τον απλό κανόνα όποιο brand περιέχεται μέσα σε άλλο brand θα πρέπει να θεωρηθεί ως βασικό στο οποίο γίνεται αναφορά ή υπάρχει λανθασμένη τιμή από τον ιδιοκτήτη των δεδομένων (Βλέπε bosch, boss) Υπάρχουν και τα παραδείγματα της λέξης EA που σαν γράμματα βρίσκεται σε αρκετούς τίτλους brand αλλά είναι και brand από μόνη της. Αυτό περιμένουμε να το ξεχωρίσουμε αργότερα όταν το μοντέλο μας θα βλέπει τα άλλα brand μέσα σε τίτλους αλλά θα βλέπει και το EA σαν brand

G = nx.DiGraph()

len(result_dict.values())
for result_key, result_list in result_dict.items():
    G.add_node(result_list["main"]["brand_uri"], label=result_list["main"]["name"])
    for dep_brand in result_list["contained"]:
        G.add_node(dep_brand["brand_uri"], label=dep_brand["name"])
        G.add_edge(dep_brand["brand_uri"], result_list["main"]["brand_uri"])

for brand_degree in G.degree():
    print(brand_degree)

no_in_brands = [
    G.nodes[brand]["label"] for brand, degree in G.in_degree() if degree == 0
]
# no incoming connections / end brands
in_brands = [G.nodes[brand]["label"] for brand, degree in G.in_degree() if degree > 0]
# incoming connection /brands that are referenced

no_out_brands = [
    G.nodes[brand]["label"] for brand, degree in G.out_degree() if degree == 0
]
# no outgoing connections / master brands /only referenced not refering others
out_brands = [G.nodes[brand]["label"] for brand, degree in G.out_degree() if degree > 0]
# outgoing connections / brands that reference other brands

# μπορούμε να βγάλουμε συμπεράσματα από τους παραπάνω πίνακες

# Μετατροπή του γράφου σε rdf
# Create an RDF graph
rdf_graph = Graph()

# Iterate over the nodes and edges of the NetworkX graph
for node in brands:
    rdf_graph.add(
        (
            URIRef(node["brand_uri"]),
            URIRef("http://magelon.com/ontologies/tags#hasTag"),
            Literal("valid"),
        )
    )

for remove_brand in brands_to_remove:
    rdf_graph.add(
        (
            URIRef(remove_brand["brand_uri"]),
            URIRef("http://magelon.com/ontologies/tags#hasTag"),
            Literal("invalid"),
        )
    )

for edge in G.edges:
    node1, node2 = edge
    rdf_graph.add(
        (
            URIRef(node1),
            URIRef("http://magelon.com/ontologies/brand#refers"),
            URIRef(node2),
        )
    )

rdf_graph.serialize(format="ttl", destination="office_valid_brands.ttl")
# rdf_graph.serialize(format="ttl", destination="valid_brands.ttl")

virtuoso.save(rdf_graph)

net = Network("1000px", "1900px", directed=False, font_color="white", bgcolor="#111111")
net.from_nx(G)
net.show("merchant_brand.html", notebook=False)

flattened_list = set([item for sublist in result_dict.values() for item in sublist])
print(duplicates)
