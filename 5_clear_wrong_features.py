from classes.VirtuosoWrapper import VirtuosoWrapper
import re
import networkx as nx
from node2vec import Node2Vec
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.cluster import AgglomerativeClustering
import numpy as np

query = """
SELECT ?product_title COUNT(DISTINCT ?attribute_title) AS ?attribute_count GROUP_CONCAT(Distinct ?brand_title; separator=", ") as ?brand GROUP_CONCAT(DISTINCT ?attribute_title; separator=", ") as ?labels 
WHERE{
?product <http://magelon.com/ontologies/products#brand> ?brand_uri ;
            <http://magelon.com/ontologies/products#title> ?product_title .
?brand_uri <http://magelon.com/ontologies/brands#brand> ?brand_title.
?attribute a <http://magelon.com/ontologies/attributes>;
    rdfs:label ?attribute_title.
?product ?p ?attribute.
}
group by ?product_title
"""

categories_query = """
SELECT ?category_uri ?category_name ?full_path
where {
 ?category_uri a <http://magelon.com/ontologies/google_categories>; 
   <http://magelon.com/ontologies/google_categories#full_path> ?full_path;
   rdfs:label ?category_name.
}
"""

attributes_query = """
PREFIX magelon: <http://magelon.com/ontologies/>
SELECT *
where{
 ?attribute a magelon:attributes.
 ?attribute rdfs:label ?attribute_label.
}
"""

virtuoso = VirtuosoWrapper()
products_result = virtuoso.getAll(query)


product_titles = []


G = nx.DiGraph()
removals = {}

for row in products_result:
    labels = [attr.strip() for attr in row["labels"].split(",")]
    print(row["product_title"])
    title = re.sub(r"[>#+'?$%^*®™()]+|-", "", row["product_title"])
    title = title.lower()
    product_titles.append(title)
    G.add_node(title)
    for label in labels:
        if re.search(label, title, re.DOTALL):
            G.add_edge(title, label)
        else:
            if title not in removals.keys():
                removals[title] = []
            removals[title].append(label)

# attributes_result = virtuoso.getAll(attributes_query)
# attributes_list = [row["attribute_label"] for row in attributes_result]
# attributes_list = []
product_titles = [row["product_title"] for row in products_result]
attributes_list = [row["labels"].split(",") for row in products_result]

# Create a feature matrix (2-dimensional array) for clustering
# In this example, we use one-hot encoding for features
features = np.zeros(
    (
        len(product_titles),
        len(
            set(attribute for attributes in attributes_list for attribute in attributes)
        ),
    )
)

for i, attributes in enumerate(attributes_list):
    for attribute in attributes:
        feature_index = list(
            set(attribute for attributes in attributes_list for attribute in attributes)
        ).index(attribute)
        features[i, feature_index] = 1


agglomerative = AgglomerativeClustering(
    n_clusters=30
)  # Set the number of clusters as desired
cluster_labels = agglomerative.fit_predict(features)

# Get the clusters and their products
clusters = {}
for i, label in enumerate(cluster_labels):
    product = product_titles[i]
    if label not in clusters:
        clusters[int(label)] = []
    clusters[int(label)].append(product)

with open("storage/agglo-clusters.json", "w") as json_file:
    json.dump(clusters, json_file)

categories_result = virtuoso.getAll(categories_query)
category_names = {}
category_paths = {}
for row in categories_result:
    category_paths[row["category_uri"]] = row["full_path"]
    category_names[row["category_uri"]] = row["category_name"]

for i, products in clusters.items():
    path_scores = []
    cluster_keywords = []
    for product in products:
        cluster_keywords.extend(re.findall(r"\b(\w+-?\w+)\b", product))
    for category_uris, category_path in category_paths.items():
        path_words = re.findall(r"\b(\w+-?\w+)\b", category_path)
        path_score = 0
        for word in path_words:
            if word.lower() in set(cluster_keywords):
                path_score += 1.0 / len(path_words)
        path_scores.append((path_score, category_path))
    top_three_paths = sorted(path_scores, key=lambda x: x[0], reverse=True)
    print(products[0:3])
    print(top_three_paths[0:3])
    input("Check paths")
# for each cluster find words that relates the products to a category


for attribute in attributes:
    if attribute in category_names:
        print(attribute)

matching_categories = {}

# Create a regex pattern to match any string in the first array
for attribute in attributes:
    if len(attribute.split()) > 1:
        pattern = "|".join(map(re.escape, attribute.split()))
    else:
        pattern = attribute
    # Combine the pattern using the '|' (OR) operator
    regex = re.compile(pattern)
    # Check if any category in the second array matches the regex pattern
    matches = [category for category in category_names if regex.search(category)]
    if len(matches) > 0:
        matching_categories[attribute] = matches
