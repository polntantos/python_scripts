import pymysql
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
from rdflib import Graph, URIRef, Literal, BNode, Namespace, RDF, RDFS
import warnings
from sklearn.exceptions import ConvergenceWarning
from sklearn.cluster import AgglomerativeClustering
import json


# Connect to MySQL database
def connect_to_database():
    return pymysql.connect(
        host="192.168.10.30", user="homestead", password="secret", db="homestead"
    )


# Get all distinct brands from database
def get_distinct_brands(cursor):
    print("Getting brands")
    cursor.execute(
        "SELECT DISTINCT brand FROM products WHERE brand IN ('xiaomi','lenovo')"
    )
    return [row[0] for row in cursor.fetchall()]


# Get products from the database for a given brand
def get_products_by_brand(cursor, brand):
    print(f"Getting products by brand {brand}")
    cursor.execute("SELECT title, description FROM products WHERE brand = %s", (brand,))
    return cursor.fetchall()


def get_silhouette_score(X, labels):
    num_labels = len(set(labels))
    if num_labels > 1:
        score = silhouette_score(X, labels)
    else:
        score = 0
    return score


# Perform clustering on product titles
def perform_clustering(titles):
    # Generate TF-IDF features
    print(f"Clusterring {len(titles)} product titles")
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(titles)

    # Find optimal number of clusters using elbow method
    # if X.shape[0] > 20:
    #   n_clusters = range(2, 20)
    # else:
    steps = [s for s in [1000, 250, 100, 25, 10, 1] if s < X.shape[0]]
    cursor = 1
    for step in steps:
        n_clusters = range(cursor, X.shape[0], step)

        sil_scores = []
        for n in n_clusters:
            cursor = n
            print(f"Now at {n} within {n_clusters}")
            try:
                kmeans = KMeans(n_init="auto", n_clusters=n, random_state=42).fit(X)
                # kmeans.labels_
            except ConvergenceWarning:
                print(f"n_clusters: {n} overpassed found clusters")
                cursor -= step
                sil_scores.append(get_silhouette_score(X, kmeans.labels_))
                break

        sil_scores.append(get_silhouette_score(X, kmeans.labels_))

    best_n = n_clusters[sil_scores.index(max(sil_scores))]

    # Cluster products using KMeans algorithm
    kmeans = KMeans(n_clusters=best_n, random_state=42).fit(X)

    # Collect keywords for each cluster MUST copy this to function
    clusters_keywords = {}
    for i, label in enumerate(kmeans.labels_):
        title = titles[i]
        keyword_lists = vectorizer.inverse_transform(X[i])[0]
        label_keywords = set([keyword_list for keyword_list in keyword_lists])
        print([label, title, label_keywords])

        if len(label_keywords) > 0:
            if label in clusters_keywords:
                clusters_keywords[label] = set(
                    [*clusters_keywords[label], *label_keywords]
                )
            else:
                clusters_keywords[label] = label_keywords

    return kmeans.labels_, clusters_keywords


# Store product clusters in RDF graph
def store_clusters_in_graph(graph, brand, titles, clusters):
    print("clusters")
    print(clusters)
    # Define RDF namespaces
    ns = Namespace("http://example.org/ontology#")
    rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

    # Create a blank node for the brand
    brand_node = BNode()

    # Add brand node to graph
    graph.add((brand_node, RDF.type, ns.Brand))
    graph.add((brand_node, ns.hasName, Literal(brand)))

    # Add product nodes to graph with corresponding clusters
    for i, title in enumerate(titles):
        print(f"index {i} title {title}")
        product_node = URIRef("http://example.org/product/" + str(i))
        graph.add((product_node, RDF.type, ns.Product))
        graph.add((product_node, ns.hasTitle, Literal(title)))
        graph.add((product_node, ns.hasCluster, Literal(clusters[i])))

        # Connect product node to brand node
        graph.add((brand_node, ns.hasProduct, product_node))

    return graph


# Main function to run the clustering algorithm and store results in RDF graph
def main():
    # Connect to database
    warnings.filterwarnings(action="ignore", category=ConvergenceWarning)
    warnings.filterwarnings(action="ignore", category=FutureWarning)
    db = connect_to_database()
    cursor = db.cursor()

    # Get distinct brands from database
    brands = get_distinct_brands(cursor)

    # Loop through each brand and perform clustering
    for brand in brands:
        # Get products for the brand
        products = get_products_by_brand(cursor, brand)

        # Group products with similar titles together
        titles = [product[0] for product in products]
        # clusters,cluster_keywords = perform_clustering(titles)
        clusters = perform_agglomerative_clusterring(titles)
        with open(f"clusters/{brand}-clusters.json", "w") as f:
            json.dump(clusters, f)
        # exit()
        # print(cluster_keywords)

        # Store clusters in RDF graph
        # graph = Graph()
        # graph.bind('ns', Namespace('http://example.org/ontology#'))
        # graph = store_clusters_in_graph(graph, brand, titles, clusters)

        # Serialize RDF graph to file
        # graph.serialize(destination=f"rdf_output/{brand} product_groups.rdf", format='xml')


def perform_agglomerative_clusterring(titles):
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(titles)
    # Z = linkage(X.toarray(), 'ward')

    # fig = plt.figure(figsize=(25, 10))
    # dn = dendrogram(Z)
    # plt.show()

    clustering = AgglomerativeClustering(
        n_clusters=None, distance_threshold=0.2, linkage="ward"
    )
    cluster_labels = clustering.fit_predict(X.toarray())
    clusters = {}

    for i, cluster_label in enumerate(cluster_labels):
        if cluster_label not in clusters:
            clusters[cluster_label.item()] = []
        clusters[cluster_label.item()].append(titles[i])

    print(clusters)
    return clusters


main()
