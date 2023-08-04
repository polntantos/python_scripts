from classes.VirtuosoWrapper import VirtuosoWrapper
import re
import networkx as nx
from sklearn.cluster import AgglomerativeClustering
import numpy as np
import json

query = """
SELECT ?product_title GROUP_CONCAT(DISTINCT ?product; separator=",") as ?product_uris  COUNT(DISTINCT ?attribute_title) AS ?attribute_count GROUP_CONCAT(Distinct ?brand_title; separator=", ") as ?brand GROUP_CONCAT(DISTINCT ?attribute_title; separator=", ") as ?labels 
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

virtuoso = VirtuosoWrapper()
products_result = virtuoso.getAll(query)


product_titles = []
product_title_dict={}

for row in products_result:
    labels = [attr.strip() for attr in row["labels"].split(",")]
    product_titles.append(row["product_title"])
    product_title_dict[row["product_title"]]=row['product_uris'].split(",")

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
    n_clusters=30,
    compute_full_tree=False,
)  # Set the number of clusters as desired
cluster_labels = agglomerative.fit_predict(features)

# Get the clusters and their products
clusters = {}
for i, label in enumerate(cluster_labels):
    product = product_titles[i]
    if label not in clusters:
        clusters[int(label)] = {"product_titles":[],"product_uris":[]}
    clusters[int(label)]["product_titles"].append(product)
    clusters[int(label)]["product_uris"].append(product_title_dict[product])

with open("storage/agglo-clusters.json", "w") as json_file:
    json.dump(clusters, json_file)