from classes.VirtuosoWrapper import VirtuosoWrapper
import re
# from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import networkx as nx
from classes.VirtuosoWrapper import VirtuosoWrapper
from pyvis.network import Network
from rdflib import Graph, URIRef, RDFS, Literal
from slugify import slugify

def evaluate_string(string):
    score = 0
    symbol_count = sum(1 for char in string if char.isalpha())
    capital_count = sum(1 for word in string.split() if word[0].isupper() and word[1:].islower())
    score += symbol_count+capital_count
    if "-" in string:
        score -= 2
    if "/" in string:
        score += 2
    words = string.split("/")
    for word in words:
        if " " in word and len(word.split(" ")) > 1:
            score += 1
    return score

def contains_duplicate_word(string):
    words = string.split()
    unique_words = set(words)
    if len(words) != len(unique_words):
      print(words,unique_words,len(words),len(unique_words), string)
    return len(words) != len(unique_words)

virtuoso = VirtuosoWrapper()

colors_query = """
  SELECT ?color ?product_count
  WHERE {
    {
      SELECT ?color (COUNT(?s) as ?product_count) 
      WHERE {
          ?s a <http://omikron44/ontologies/products>.
          ?s <http://omikron44/ontologies/products#color> ?color.
      }
      GROUP BY ?color
      ORDER BY DESC(?product_count )
    }
  }
    """

# Δουλεύουμε με αυτό το query ώστε τα offset και limit που θα μπουν από τη wrapper κλάση να μην μας επηρεάσουν

colors = virtuoso.getAll(colors_query)

colors_to_remove = []

for color in colors:
  if re.search(r"[>#+'?$%^*®™()]+", color["color"]):
    colors_to_remove.append(color)
  elif re.search(r"[0-9]+", color["color"]):
    colors_to_remove.append(color)  
  elif len(color["color"].split())>1 :
    for value in color["color"].split():
      if len(value)>40:
        colors_to_remove.append(color)
        break
  elif len(color['color'])>100:
    colors_to_remove.append(color)
  elif contains_duplicate_word(color['color']):
    colors_to_remove.append(color)

colors = [color for color in colors if color not in colors_to_remove]

# print(f"Total colors:{len(colors)}")
# print(f"Total colors_to_remove:{len(colors_to_remove)}")

transformed_array = [
    re.sub(r"[^a-z0-9]+", "", color["color"].lower())
    for color in colors
    if not re.search(r"[>#?$%^&*()]+", color["color"])
]

duplicates = {}
for value in colors:
    term = re.sub(r"[^a-zA-Z]+", "", value["color"].lower())
    if transformed_array.count(term) > 1:
        if term not in duplicates:
            duplicates[term] = []
        duplicates[term].append(value)

duplicate_remains = []
# turn to rule based selection of duplicates
for dupli_name, duplicate_array in duplicates.items():
    color_scores = {}
    for index, duplicate_color in enumerate(duplicate_array):
        term_score = evaluate_string(duplicate_color["color"])
        # print(f"{index} : {term_score} : {duplicate_color['color']}")
        color_scores[index] = term_score
    max_key = max(color_scores, key=lambda k: color_scores[k])
    # print(f"selected key {max_key}")
    duplicate_remains.append(duplicate_array[int(max_key)])

duplicate_invalidates = []
for dupli_name, duplicate_array in duplicates.items():
    for index, duplicate_color in enumerate(duplicate_array):
        if duplicate_color not in duplicate_remains:
            # print(duplicate_color)
            duplicate_invalidates.append(duplicate_color)

for duplicate_invalidate in duplicate_invalidates:
    if duplicate_invalidate in colors:
        colors_to_remove.append(colors.pop(colors.index(duplicate_invalidate)))
print(f"Duplicate remains {len(duplicate_remains)}")
print(f"Total colors:{len(colors)}")
print(f"Total colors_to_remove:{len(colors_to_remove)}")

result_dict = {}
# check if valid colors are contained in other colors
for i, value in enumerate(colors):
    print(f"current key {i}")
    contained_values = []
    for j, other_value in enumerate(colors):
        if (
            i != j
            and value["color"].lower() in other_value["color"].lower()
            and value["color"] != ""
        ):
            if len(other_value["color"].split()) > 1 and len(value["color"].split()) == 1:
                if value["color"].lower() in other_value["color"].lower().split():
                    contained_values.append(other_value)
            elif len(other_value["color"].split()) == 1 and len(value["color"].split()) == 1:
                if value["color"].lower() == other_value["color"].lower():
                    contained_values.append(other_value)
            else:
                contained_values.append(other_value)
    print(contained_values)
    if len(contained_values) > 0:
        result_dict[value["color"]] = {}
        result_dict[value["color"]]["main"] = value
        result_dict[value["color"]]["contained"] = contained_values

# print(result_dict)

G = nx.DiGraph()

# len(result_dict.values())
for result_key, result_list in result_dict.items():
    G.add_node(result_list["main"]["color"])
    for dep_color in result_list["contained"]:
        G.add_node(dep_color["color"])
        G.add_edge(dep_color["color"], result_list["main"]["color"])

for color_degree in G.degree():
    print(color_degree)

no_in_colors = [color for color, degree in G.in_degree() if degree == 0]
# no incoming connections / end colors
in_colors = [color for color, degree in G.in_degree() if degree > 0]
# incoming connection /colors that are referenced

no_out_colors = [color for color, degree in G.out_degree() if degree == 0]
# no outgoing connections / master colors /only referenced not refering others
out_colors = [color for color, degree in G.out_degree() if degree > 0]
# outgoing connections / colors that reference other colors

# print(in_colors)
# print(out_colors)

# print(no_in_colors)
# print(no_out_colors)


# Create an RDF graph
rdf_graph = Graph()

# Iterate over the nodes and edges of the NetworkX graph
for node in colors:
    rdf_graph.add(
        (
            URIRef(base="http://omikron44/ontologies/colors/",value=slugify(node["color"])),
            RDFS.label,
            Literal(node["color"]),
        )
    )

for remove_brand in colors_to_remove:
    rdf_graph.add(
        (
            URIRef(base="http://omikron44/ontologies/colors/",value=slugify(node["color"])),
            RDFS.label,
            Literal(node["color"]),
        )
    )
    rdf_graph.add((
            URIRef(base="http://omikron44/ontologies/colors/",value=slugify(node["color"])),
            URIRef("http://omikron44/ontologies/tags#hasTag"),
            Literal("invalid"),
        )
    )

for edge in G.edges:
    node1, node2 = edge
    rdf_graph.add(
        (
            URIRef(base="http://omikron44/ontologies/colors/",value=slugify(node1)),
            URIRef("http://omikron44/ontologies/color#refers"),
            URIRef(base="http://omikron44/ontologies/colors/",value=slugify(node2))
        )
    )

rdf_graph.serialize(format="ttl", destination="office_colors.ttl")
# rdf_graph.serialize(format="ttl", destination="valid_brands.ttl")

# virtuoso.save(rdf_graph)

net = Network("1000px", "1900px", directed=False, font_color="white", bgcolor="#111111")
net.from_nx(G)
net.show("office_colors.html", notebook=False)
