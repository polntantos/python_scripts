import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from classes.VirtuosoWrapper import VirtuosoWrapper

virtuoso = VirtuosoWrapper()
# Step 1: Fetch the product titles and IDs from Virtuoso
# get brands
brands_query = """
SELECT ?brand_uri ?name
WHERE {
  ?brand_uri a <http://omikron44/ontologies/brands> .
  ?brand_uri <http://omikron44/ontologies/brands#brand> ?name .
}
"""
brands = virtuoso.get(brands_query)
# print(brands)

for brand in brands["results"]["bindings"]:
    brand_uri = brand["brand_uri"]["value"]

    if brand["name"]["value"] == "":
        continue

    print(f"working on brand {brand['name']['value']} with URI {brand_uri}")

    products_query = f"""
        SELECT ?product_uri ?title
        WHERE {{
            ?product_uri a <http://omikron44/ontologies/products> .
            ?product_uri <http://omikron44/ontologies/products#title> ?title.
            ?product_uri <http://omikron44/ontologies/products#brand> <{brand_uri}> .
        }}
    """

    products_result = virtuoso.get(products_query)
    print(len(products_result["results"]["bindings"]))

    if len(products_result["results"]["bindings"]) < 2:
        continue

    # Step 2: Preprocess the data
    prod_uris = []
    prod_titles = []
    for prod in products_result["results"]["bindings"]:
        prod_uris.append(prod["product_uri"]["value"])
        prod_titles.append(prod["title"]["value"])

    # Step 3: Vectorize the data
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(prod_titles)

    # Step 4: Perform clustering
    clusterer = AgglomerativeClustering(
        n_clusters=None, distance_threshold=0.7, linkage="ward"
    )
    cluster_labels = clusterer.fit_predict(X.toarray())

    # Step 5: Group the titles and IDs by cluster label
    clusters = {}
    for i, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[str(label)] = []
        clusters[str(label)].append({"title": prod_titles[i], "id": prod_uris[i]})

    print(clusters)
    print(type(clusters))
    # Step 6: Dump the clusters in JSON format
    with open(f"clusters/" + brand["name"]["value"] + "-clusters.json", "w") as f:
        json.dump(obj=clusters, fp=f, indent=4)
