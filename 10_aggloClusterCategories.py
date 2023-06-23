import json
import pymysql
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from rdflib import Graph, URIRef, Literal, BNode, Namespace, RDF, RDFS
import matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
from classes.VirtuosoWrapper import VirtuosoWrapper


def get_distinct_categories():
    print("Getting categories")
    virtuoso = VirtuosoWrapper()
    query = """
    SELECT DISTINCT ?product_type
        WHERE {
        ?p a <http://omikron44/ontologies/products>.
        ?p <http://omikron44/ontologies/products#brand> ?brand .
        ?brand a <http://omikron44/ontologies/brands>.
        ?brand <http://omikron44/ontologies/tags#hasTag> "valid".
        ?p <http://omikron44/ontologies/products#product_type> ?product_type .
        }
    """
    # We will use only categories from products that are connected to official brands
    response = virtuoso.get(query)

    return [
        category["product_type"]["value"]
        for category in response["results"]["bindings"]
    ]


def perform_agglomerative_clusterring(categories, display=False):
    print(f"Clustering {len(categories)} categories")
    # exit()
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(categories)

    if display:
        Z = linkage(X.toarray(), "ward")

        plt.figure(figsize=(25, 10))
        dendrogram(Z)
        plt.show()

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=2,
        linkage="ward",
    )

    cluster_labels = clustering.fit_predict(X.toarray())
    clusters = {}

    for i, cluster_label in enumerate(cluster_labels):
        if cluster_label not in clusters:
            clusters[cluster_label.item()] = []
        clusters[cluster_label.item()].append(categories[i])

    print(clusters)
    return clusters


def main():
    categories = get_distinct_categories()
    clusters = perform_agglomerative_clusterring(categories)
    with open(f"clusters/category-clusters.json", "w") as f:
        myKeys = list(clusters.keys())
        myKeys.sort()
        sorted_dict = {i: clusters[i] for i in myKeys}
        json.dump(sorted_dict, f)


main()
