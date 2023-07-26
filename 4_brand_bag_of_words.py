from classes.VirtuosoWrapper import VirtuosoWrapper
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import nltk
from nltk.corpus import stopwords
from rdflib import Graph, URIRef, RDF, RDFS,Literal
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

def get_data(brand_name):
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
    return response

def create_feature_word_graph(product_titles):
    G = nx.DiGraph()
    for product_title in product_titles:
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
    return G

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

def get_all_paths(G:nx.DiGraph):
    all_paths = []
    for node1 in G.nodes():
        for node2 in G.nodes():
            if node1 != node2:
                all_paths.extend(get_most_common_paths(G,node1,node2))
    return all_paths

def assign_product_features(product_titles,sorted_paths,top_paths_count):
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
    return features_in_products, product_features

def extract_extra_keywords(brand_name,mpns,colors):
    stopwords_list = stopwords.words("english")
    stopwords_list.extend([brand_name, brand_name.lower()])
    stopwords_list.extend(map(lambda x: x.lower(), mpns))
    stopwords_list.extend(map(lambda x: x.lower(), colors))
    vectorizer = TfidfVectorizer(
        stop_words=stopwords_list, ngram_range=(1, 2), min_df=1, max_df=0.5
    )
    X = vectorizer.fit_transform(product_titles)
    vocab = [word for word in vectorizer.vocabulary_]
    return vocab

def filter_small_words_numbers(vocab):
    filtered_vocab = []
    for word in vocab:
        if word.isdigit() and len(word) <= 3:
            continue
        if word.isalpha() and len(word) <= 2:
            continue
        filtered_vocab.append(word)
    return filtered_vocab

def extend_feature_vocabs(filtered_vocab,product_titles,product_features,features_in_products):
    for word in filtered_vocab:
        if slugify(word) in product_features:
            continue
        for product_title in product_titles:
            title= re.sub(r"[>#+'?$%^*®™()]+|-","",product_title)
            title = " ".join(title.lower().split())
            if word in title:
                if title not in features_in_products:
                    features_in_products[title]=[]
                features_in_products[title].append(word)
                if slugify(word) not in product_features.keys():
                    product_features[slugify(word)]= 0
                product_features[slugify(word)]=product_features[slugify(word)]+1
    return features_in_products,product_features

def generate_product_dict(response,brand_name,mpns,colors,features_in_products):
    product_dict = {}
    for row in response:
        transformed_title = row["product_title"].lower()
        cleared_title = re.sub(r"[>#+'?$%^*®™()]+|-","",row["product_title"].lower())
        product_dict[row["product"]] = {"product_title": row["product_title"]}
        if brand_name.lower() in transformed_title.split():
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
        if(cleared_title in features_in_products):
            product_dict[row["product"]]["features"]=set(features_in_products[cleared_title])
    return product_dict

def create_rdf_graph(product_dict):
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
    return graph

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
virtuoso = VirtuosoWrapper()
response_colors = virtuoso.getAll(color_query)
colors = set([row["label"] for row in response_colors])

brand_name = "Apple"
response = get_data(brand_name)

product_titles = [row["product_title"] for row in response]
mpns = set([row["mpn"] for row in response])
G=create_feature_word_graph(product_titles=product_titles)
all_paths=get_all_paths(G=G)
sorted_paths = sorted(all_paths,key=lambda x:x['path_score'],reverse=True)
top_paths_count = math.ceil(len(sorted_paths)/100)*30#top 30%
features_in_products ,product_features =assign_product_features(product_titles,sorted_paths,top_paths_count)
vocab = extract_extra_keywords(brand_name,mpns,colors)
filtered_vocab = filter_small_words_numbers(vocab)
features_in_products,product_features=extend_feature_vocabs(
    filtered_vocab,
    product_titles,
    product_features,
    features_in_products
)
product_dict = generate_product_dict(response,brand_name,mpns,colors,features_in_products)
graph = create_rdf_graph(product_dict)
# store rdf data
virtuoso.save(graph)
graph.serialize(f"storage/{brand_name}_feature_graph.ttl",format="ttl") # if you want to see the rdf