from classes.VirtuosoWrapper import VirtuosoWrapper
import re

# from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import networkx as nx
from classes.VirtuosoWrapper import VirtuosoWrapper
from pyvis.network import Network
from rdflib import Graph, URIRef, RDFS, RDF, Literal
from slugify import slugify


def evaluate_string(string):
    score = 0
    symbol_count = sum(1 for char in string if char.isalpha())
    capital_count = sum(
        1 for word in string.split() if word[0].isupper() and word[1:].islower()
    )
    score += symbol_count + capital_count
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
        print(words, unique_words, len(words), len(unique_words), string)
    return len(words) != len(unique_words)


def clean_words(string):
    words = []
    word = ""
    for letter in string:
        if letter.isalpha():
            word += letter
        else:
            words.append(word)
            word = ""
    if word != "":
        words.append(word)
    return words


def create_graph_vis(graph, name="graph_vis", ego=None, distance=1):
    net = Network(
        "1000px", "1900px", directed=False, font_color="white", bgcolor="#111111"
    )
    if ego != None:
        graph = nx.ego_graph(graph, ego, radius=distance, undirected=True)
        name = f"{name}_{ego}"
    net.from_nx(graph)
    net.show(
        f"{name}.html",
        notebook=False,
    )


def get_degree_arrays(graph):
    no_incoming = [
        (color, degree) for color, degree in graph.in_degree() if degree == 0
    ]
    # no incoming connections / end colors
    incoming = [(color, degree) for color, degree in graph.in_degree() if degree > 0]
    # incoming connection /colors that are referenced
    no_outgoing = [
        (color, degree) for color, degree in graph.out_degree() if degree == 0
    ]
    # no outgoing connections / master colors /only referenced not refering others
    outgoing = [(color, degree) for color, degree in graph.out_degree() if degree > 0]
    return no_incoming, incoming, no_outgoing, outgoing


virtuoso = VirtuosoWrapper()

colors_query = """
  SELECT ?color ?product_count
  WHERE {
    {
      SELECT ?color (COUNT(?s) as ?product_count) 
      WHERE {
          ?s a <http://magelon.com/ontologies/products>.
          ?s <http://magelon.com/ontologies/products#color> ?color.
      }
      GROUP BY ?color
      ORDER BY DESC(?product_count )
    }
  }
    """

# Δουλεύουμε με αυτό το query ώστε τα offset και limit που θα μπουν από τη wrapper κλάση να μην μας επηρεάσουν

colors = virtuoso.getAll(colors_query)

print(f"Total color values: {len(colors)}")

single_colors = [color["color"].lower() for color in colors if color["color"].isalpha()]

print(f"Basic colors extracted:{len(single_colors)}")
single_colors = set(single_colors)  # keep unique values
single_colors = [
    color for color in single_colors if len(color) > 2
]  # keep unique values

# we extracted these manually with inspection
known_variation_stopwords = [
    "light",
    "dark",
    "striped",
    "soft",
    "deep",
    "medium",
    "checked",
    "faded",
    "stripped",
    "stars",
]

peer_validated_colors = []
for db_color in colors:
    check_color = db_color["color"].lower()
    for color in single_colors:
        if color != check_color and color in check_color:
            peer_validated_colors.append(color)

peer_validated_colors = set(peer_validated_colors)
peer_validated_colors = [
    color for color in peer_validated_colors if color not in known_variation_stopwords
]

rdf_graph = Graph()

print(f"Total colors validated by peers : {len(single_colors)}")

# Iterate over the nodes and edges of the NetworkX graph
for color in peer_validated_colors:
    rdf_graph.add(
        (
            URIRef(base="http://magelon.com/ontologies/colors/", value=color),
            RDFS.label,
            Literal(color.capitalize()),
        )
    )
    rdf_graph.add(
        (
            URIRef(base="http://magelon.com/ontologies/colors/", value=color),
            RDF.type,
            URIRef("http://magelon.com/ontologies/colors"),
        )
    )
    rdf_graph.add(
        (
            URIRef(base="http://magelon.com/ontologies/colors/", value=color),
            RDF.type,
            URIRef("http://magelon.com/ontologies/basic_colors"),
        )
    )

colors = [
    color for color in colors if color["color"].lower() not in peer_validated_colors
]

colors_to_remove = []

for color in colors:
    if re.search(r"[>#+'?$%^*®™()]+", color["color"]):
        colors_to_remove.append(color)
    elif re.search(r"[0-9]+", color["color"]):
        colors_to_remove.append(color)
    elif len(color["color"].split()) > 1:
        for value in color["color"].split():
            if len(value) > 40:
                colors_to_remove.append(color)
                break
    elif len(color["color"]) > 100:
        colors_to_remove.append(color)

colors = [color for color in colors if color not in colors_to_remove]

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

colors = [color for color in colors if color not in colors_to_remove]

print(f"Duplicate remains {len(duplicate_remains)}")
print(f"Total colors:{len(colors)}")
print(f"Total colors removed:{len(colors_to_remove)}")

# Check for variations split by "/"
variations = {}

for color in colors:
    c_color = color["color"].lower()
    if "/" in c_color:
        color_parts = c_color.split("/")
        for part in color_parts:
            words = clean_words(part)
            for word in words:
                if (
                    word in peer_validated_colors
                    and part.strip() not in peer_validated_colors
                ):
                    if word not in variations.keys():
                        variations[word] = []
                    if part.strip() not in variations[word]:
                        variations[word].append(part.strip())

# build the graph with the variations to check if they are mixed colors
variations_graph = nx.DiGraph()

for valid, variation_arr in variations.items():
    for variation in variation_arr:
        variations_graph.add_edge(variation, valid)

print(f"Total colors kept by peer {len(peer_validated_colors)}")
secondary_colors = []
secondary_colors.extend([sec_array for sec_array in variations.values()])
print(f"Total colors kept by connection to peer {len(secondary_colors)}")

show_examples = input("Wanna see graph visual examples?[Y/n]")
if show_examples == "y" or show_examples == "Y" or show_examples == "":
    create_graph_vis(variations_graph, "color_variations_graph", "pink")
    create_graph_vis(variations_graph, "color_variations_graph", "black")
    create_graph_vis(variations_graph, "color_variations_graph", "white")

no_incoming, incoming, no_outgoing, outgoing = get_degree_arrays(variations_graph)

color_variations = [color for color, degree in outgoing if degree == 1]
color_mixtures = [color for color, degree in outgoing if degree > 1]

rdf_graph.serialize(format="ttl", destination="basic_colors.ttl")

for edge in variations_graph.edges:
    refering_color, refered_color = edge
    rdf_graph.add(
        (
            URIRef(
                base="http://magelon.com/ontologies/colors/",
                value=slugify(refering_color),
            ),
            RDFS.label,
            Literal(refering_color.capitalize()),
        )
    )
    rdf_graph.add(
        (
            URIRef(
                base="http://magelon.com/ontologies/colors/",
                value=slugify(refering_color),
            ),
            URIRef("http://magelon.com/ontologies/color#refers"),
            URIRef(
                base="http://magelon.com/ontologies/colors/",
                value=slugify(refered_color),
            ),
        )
    )
    rdf_graph.add(
        (
            URIRef(
                base="http://magelon.com/ontologies/colors/",
                value=slugify(refering_color),
            ),
            RDF.type,
            URIRef("http://magelon.com/ontologies/colors"),
        )
    )
    if refering_color in color_variations:
        rdf_graph.add(
            (
                URIRef(
                    base="http://magelon.com/ontologies/colors/",
                    value=slugify(refering_color),
                ),
                RDF.type,
                URIRef("http://magelon.com/ontologies/color_variations"),
            )
        )
    if refering_color in color_mixtures:
        rdf_graph.add(
            (
                URIRef(
                    base="http://magelon.com/ontologies/colors/",
                    value=slugify(refering_color),
                ),
                RDF.type,
                URIRef("http://magelon.com/ontologies/mixture_colors"),
            )
        )

# checkpoint
rdf_graph.serialize(format="ttl", destination="basic_full_colors.ttl")

save_input = input("Hit 'Y' and commit to save your colors :")
if save_input == "Y":
    virtuoso.save(rdf_graph)