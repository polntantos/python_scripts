import json
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from classes.VirtuosoWrapper import VirtuosoWrapper
from rdflib import URIRef, Graph, RDF, Literal
import uuid
import time
import math
import matplotlib.pyplot as plt
import warnings 


def get_brands(offset=0):
    virtuoso = VirtuosoWrapper()
    brands_query = f"""
    SELECT ?brand_uri ?name
    WHERE {{
    ?brand_uri a <http://omikron44/ontologies/brands> .
    ?brand_uri <http://omikron44/ontologies/brands#brand> ?name .
    }} ORDER BY ?name 
    offset {offset} 
    """
    # FILTER(str(?brand_uri) = "http://omikron44/ontologies/brands/id=1385") .
    # Offset 1930
    ## offset 1929 #IWOOT
    brands = virtuoso.get(brands_query)
    return brands


def get_products(brand_uri):
    virtuoso = VirtuosoWrapper()
    offset = 0
    products_result = []
    while True:
        products_query = f"""
            SELECT ?product_uri ?title
            WHERE {{
                ?product_uri a <http://omikron44/ontologies/products> .
                ?product_uri <http://omikron44/ontologies/products#title> ?title.
                ?product_uri <http://omikron44/ontologies/products#brand> <{brand_uri}> .
            }} OFFSET {offset} LIMIT 5000
        """
        # print(products_query)

        products_query_result = virtuoso.get(products_query)
        print(
            f"fetched from db from {offset} to ",
            offset + len(products_query_result["results"]["bindings"]),
        )

        products_result.extend(products_query_result["results"]["bindings"])

        if (
            len(products_query_result["results"]["bindings"]) >= 5000
        ):  # Query max return
            offset += len(products_query_result["results"]["bindings"])
            continue
        else:
            break

    return products_result


def get_silhouette_score(X, labels):
    num_labels = len(set(labels))
    if num_labels > 1:
        score = silhouette_score(X, labels)
    else:
        score = 0
    return score


def perform_clustering(prod_titles):
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(prod_titles)

    print(f"Clustering {len(prod_titles)}")
    # Step 4: Perform clustering
    time1 = time.time()
    step = max(1, math.floor(X.shape[0] / 5))

    # n_clusters = range(10, X.shape[0], step)

    sil_scores = {}

    n_clusters = list(range(10, X.shape[0], step))

    break_flag = False
    # checked_clusters = []

    while n_clusters:
        n = n_clusters.pop(0)
        cursor = n

        print(f"Now checking {cursor} within {X.shape[0]}")

        clusterer = KMeans(
            n_clusters=cursor,
            # verbose=2,
            random_state=42,
            n_init="auto",
        ).fit(X)

        if len(set(clusterer.labels_)) < cursor:
            print(
                f"n_clusters: {n} overpassed found clusters {len(set(clusterer.labels_))} skipping to retry with {len(set(clusterer.labels_))}"
            )
            if cursor in sil_scores:
                break

            n_clusters.insert(0, len(set(clusterer.labels_)))
            break_flag = True
            continue
        # else:
            # checked_clusters.append(cursor)

        silhouette_score = get_silhouette_score(X, clusterer.labels_)
        sil_scores[cursor]=silhouette_score

        print(
            f"Appending label count {len(clusterer.labels_)} for  cluster center count {len(clusterer.cluster_centers_)} with {silhouette_score} silhouette_score"
        )
        if break_flag:
            break

    best_n = max(sil_scores, key=sil_scores.get)

    print(f"clustering with {best_n} expected clusters")
    kmeans = KMeans(n_clusters=best_n, random_state=42, verbose=2, n_init="auto").fit(X)

    cluster_labels = kmeans.fit(X.toarray())
    time2 = time.time()

    cluster_labels = clusterer.labels_
    cluster_centers = clusterer.cluster_centers_

    # plt.scatter(X.toarray()[:, 0], X.toarray()[:, 1], c=cluster_labels, cmap="viridis")

    # Plot the cluster centers
    # plt.scatter(cluster_centers[:, 0], cluster_centers[:, 1], marker="x", color="red")

    # Add labels and title to the plot
    # plt.xlabel("Feature 1")
    # plt.ylabel("Feature 2")
    # plt.title("K-means Clustering")

    # Show the plot
    # plt.show()

    print(f"Clustered in {time2-time1} seconds")
    return cluster_labels, cluster_centers


def add_cluster_to_graph(graph, subject, brand_uri, title):
    graph.add(
        (
            subject,
            RDF.type,
            URIRef("http://omikron44/ontologies/magelon-product-families"),
        )
    )

    graph.add(
        (
            subject,
            URIRef("http://omikron44/ontologies/magelon-product-families#brand"),
            URIRef(brand_uri),
        )
    )
    graph.add(
        (
            subject,
            URIRef("http://omikron44/ontologies/magelon-product-families#title"),
            Literal(title),
        )
    )


def connect_product_to_cluster(graph, subject, product_id):
    graph.add(
        (
            subject,
            URIRef("http://omikron44/ontologies/magelon-product-families#merchant-products"),
            URIRef(product_id),
        )
    )


def store_graph_results(debug, graph, brand=None):
    if debug:  ## for debug turn this to true
        graph.serialize(
            destination=f"clusters/" + brand["name"]["value"] + "-clusters.ttl"
        )
        # with open(f"clusters/" + brand["name"]["value"] + "-clusters.json", "w") as f:
        #     json.dump(obj=clusters, fp=f, indent=4)
        exit()
    else:
        virtuoso = VirtuosoWrapper()
        virtuoso.save(graph)


warnings.filterwarnings(action="ignore", category=ConvergenceWarning)

brands = get_brands(1929)
total_brands = len(brands["results"]["bindings"])
for index, brand in enumerate(brands["results"]["bindings"]):
    print(f"Brands {index} out of {total_brands}")

    brand_uri = brand["brand_uri"]["value"]

    if brand["name"]["value"] == "":
        print("skipping empty name brand")
        continue

    print(f"working on brand {brand['name']['value']} with URI {brand_uri}")

    products_result = get_products(brand_uri)
    if len(products_result) < 11:  # no reason to clster
        continue

    prod_uris = []
    prod_titles = []
    for prod in products_result:
        prod_uris.append(prod["product_uri"]["value"])
        prod_titles.append(prod["title"]["value"])

    cluster_labels,cluster_centers = perform_clustering(prod_titles)

    print(cluster_labels)
    print(cluster_centers)
    clusters = {}
    label_uris = {}

    for i,label in enumerate(cluster_labels):
        if int(label) not in clusters:
            label_uris[int(label)] = {
                "uri": f"http://omikron44/ontologies/magelon-product-families/id={uuid.uuid4()}",
                "title": prod_titles[i],
            }
            clusters[int(label)]=[]
        clusters[int(label)].append({"title": prod_titles[i], "id": prod_uris[i]})
    
    graph = Graph()
    for label in label_uris:
        subject = URIRef(label_uris[label]["uri"])
        add_cluster_to_graph(graph, subject, brand_uri, label_uris[label]["title"])
        
        for product in clusters[label]:
            connect_product_to_cluster(graph, subject, product["id"])
            
    store_graph_results(False, graph, brand)
