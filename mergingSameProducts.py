import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from classes.VirtuosoWrapper import VirtuosoWrapper
from rdflib import URIRef, Graph, RDF, Literal
import uuid
import time


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


def perform_clustering(prod_titles):
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(prod_titles)
    print(f"Clustering {len(prod_titles)}")
    # Step 4: Perform clustering
    time1 = time.time()
    clusterer = AgglomerativeClustering(
        n_clusters=None, distance_threshold=1, linkage="ward"
    )
    cluster_labels = clusterer.fit_predict(X.toarray())
    time2 = time.time()

    print(f"Clustered in {time2-time1} seconds")
    return cluster_labels


def add_cluster_to_graph(graph, subject, brand_uri, title):
    graph.add(
        (
            subject,
            RDF.type,
            URIRef("http://omikron44/ontologies/magelon-products"),
        )
    )

    graph.add(
        (
            subject,
            URIRef("http://omikron44/ontologies/magelon-products#brand"),
            URIRef(brand_uri),
        )
    )
    graph.add(
        (
            subject,
            URIRef("http://omikron44/ontologies/magelon-products#title"),
            Literal(title),
        )
    )


def connect_product_to_cluster(graph, subject, product_id):
    graph.add(
        (
            subject,
            URIRef("http://omikron44/ontologies/magelon-products#merchant-products"),
            URIRef(product_id),
        )
    )


def store_graph_results(debug, graph, brand=None):
    if debug:  ## for debug turn this to true
        graph.serialize(
            destination=f"clusters/" + brand["name"]["value"] + "-clusters.ttl"
        )
        with open(f"clusters/" + brand["name"]["value"] + "-clusters.json", "w") as f:
            json.dump(obj=clusters, fp=f, indent=4)
        exit()
    else:
        virtuoso = VirtuosoWrapper()
        virtuoso.save(graph)


# Step 1: Fetch brands, product titles and IDs from Virtuoso
brands = get_brands(1929)

for index, brand in enumerate(brands["results"]["bindings"]):
    print(f"Brands {index} out of {len(brands)}")

    brand_uri = brand["brand_uri"]["value"]

    if brand["name"]["value"] == "":
        print("skipping empty name brand")
        continue

    print(f"working on brand {brand['name']['value']} with URI {brand_uri}")

    products_result = get_products(brand_uri)

    if len(products_result) > 0:
        if len(products_result) < 2:
            graph = Graph()

            prod = products_result[0]
            subject = URIRef(
                f"http://omikron44/ontologies/magelon-products/id={uuid.uuid4()}"
            )

            add_cluster_to_graph(graph,subject,brand_uri,Literal(prod["title"]["value"]))
            connect_product_to_cluster(graph,subject,prod["product_uri"]["value"])
            virtuoso = VirtuosoWrapper
            virtuoso.save(graph)

            continue  # next brand
    else:
        continue

    # Step 2: Preprocess and break down the data
    cluster_groups = []
    for i in range(0, len(products_result), 5000):
        prod_uris = []
        prod_titles = []

        for prod in products_result[i : i + 5000]:
            prod_uris.append(prod["product_uri"]["value"])
            prod_titles.append(prod["title"]["value"])

            # Step 3: Perform clustering on title groups
        cluster_labels = perform_clustering(prod_titles)

        # Step 5: Group the groups of titles and IDs by cluster label
        clusters = {}
        cluster_titles = {}

        for i, label in enumerate(cluster_labels):
            if int(label) not in clusters:
                cluster_titles[int(label)] = prod_titles[i]
                clusters[int(label)] = []
            clusters[int(label)].append({"title": prod_titles[i], "id": prod_uris[i]})
        cluster_groups.append({"cluster_titles": cluster_titles, "clusters": clusters})

        # print(cluster_titles)
        print(cluster_titles)
        print(len(cluster_titles))
        exit()
    # print(f"init label: {label}")
    # label_uris[int(label)] = {
    #     "uri": f"http://omikron44/ontologies/magelon-products/id={uuid.uuid4()}",
    #     "title": prod_titles[i],
    # }
    # print("cluster_labels")
    # print(cluster_labels)
    # print("i,label")
    # print(i, label)
    # print("clusters")
    # print(clusters)
    # print("label_uris")
    # print(label_uris)

    # Step 6: Turn the clusters to graphs
    graph = Graph()
    for label in label_uris:
        subject = URIRef(label_uris[label]["uri"])
        # print(subject)
        add_cluster_to_graph(graph, subject, brand_uri, label_uris[label]["title"])

        for product in clusters[label]:
            connect_product_to_cluster(graph, subject, product["id"])
    # Step 7: Store the clusters
    store_graph_results(False, graph, brand)
