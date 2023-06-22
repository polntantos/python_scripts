from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from classes.VirtuosoWrapper import VirtuosoWrapper
import json


def get_brands(offset=0):
    virtuoso = VirtuosoWrapper()
    brands_query = f"""
    SELECT ?brand_uri ?name ?valid
    WHERE {{
    ?brand_uri a <http://omikron44/ontologies/brands> .
    ?brand_uri <http://omikron44/ontologies/brands#brand> ?name .
    OPTIONAL{{?brand_uri <http://omikron44/ontologies/tags#hasTag> ?valid .}}
    }} LIMIT 10000
    offset {offset} 
    """

    brands = virtuoso.get(brands_query)
    return brands


brand_ids = []
brand_values = []
valid_brands = []

while True:
    db_brands = get_brands(len(brand_values))
    for i, row in enumerate(db_brands["results"]["bindings"]):
        if "valid" in row:
            valid_brands.append(row["name"]["value"])
        brand_values.append(row["name"]["value"])
        brand_ids.append(row["brand_uri"]["value"])

    if len(db_brands["results"]["bindings"]) < 10000:
        break

# Preprocess brand values
# preprocessed_values = [value.lower().replace("#", "") for value in brand_values]

# Create TF-IDF vectors
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(brand_values)

# Apply DBSCAN clustering
eps = 0.3  # Adjust the value based on the density of your data
min_samples = 2  # Adjust the value based on the expected minimum cluster size
dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
clusters = dbscan.fit_predict(X)

# Analyze clusters
unique_clusters = set(clusters)
cluster_dict = {}
for cluster_id in unique_clusters:
    cluster_indices = [i for i, label in enumerate(clusters) if label == cluster_id]
    cluster_values = {brand_values[i]: brand_ids[i] for i in cluster_indices}
    valid_brand_names = []
    for value in cluster_values.keys():
        # print(value)
        # print(type(value))
        # exit()
        if value in valid_brands:
            contains_valid = True
            valid_brand_names.append(value)
        else:
            contains_valid = False

    print(f"Cluster {cluster_id}: {cluster_values}")
    cluster_dict[int(cluster_id)] = {
        "valid_brand_names": valid_brand_names,
        "contains_valid": contains_valid,
        "brands": cluster_values,
    }

with open(f"clusters/similar-brand-clusters.json", "w") as f:
    json.dump(cluster_dict, f)
