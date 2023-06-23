import networkx as nx
import pandas as pd
from classes.VirtuosoWrapper import VirtuosoWrapper

G = nx.DiGraph()
virtuoso = VirtuosoWrapper()

offset = 0
brand_data = []

brand_counts = {}
merchant_brand_counts = {}

while True:
    query = f"""
    SELECT ?brandName (COUNT(?product) AS ?productCount) ?merchantId
    WHERE {{
    ?brand a <http://omikron44/ontologies/brands> .
    ?product <http://omikron44/ontologies/products#brand> ?brand.
    ?product <http://omikron44/ontologies/products#merchant_id> ?merchantId.
    ?brand <http://omikron44/ontologies/brands#brand> ?brandName.
    }}
    GROUP BY ?brandName ?merchantId
    OFFSET {offset} LIMIT 10000
    """
    merchant_brands_response = virtuoso.get(query)
    for brand_data_row in merchant_brands_response["results"]["bindings"]:
        brand_data.append(
            (
                brand_data_row["brandName"]["value"],
                brand_data_row["merchantId"]["value"],
                brand_data_row["productCount"]["value"],
            )
        )
        merchant_id = brand_data_row["merchantId"]["value"]
        brand_name = brand_data_row["brandName"]["value"]
        if brand_name not in G:
            G.add_node(
                brand_name,
            )
            brand_counts[brand_name] = 0
        if merchant_id not in G:
            G.add_node(merchant_id)
            merchant_brand_counts[merchant_id] = {}
        G.add_edge(
            brand_name, merchant_id, weight=int(brand_data_row["productCount"]["value"])
        )
        merchant_brand_counts[merchant_id][brand_name] = int(
            brand_data_row["productCount"]["value"]
        )
    offset += len(merchant_brands_response["results"]["bindings"])
    print(f"current data length {offset}")
    if len(merchant_brands_response["results"]["bindings"]) < 10000:
        break

brand_centrality = nx.eigenvector_centrality_numpy(
    G.reverse(), max_iter=10000, weight="weight", tol=1e-4
)
merchant_centrality = nx.eigenvector_centrality_numpy(
    G, max_iter=10000, weight="weight", tol=1e-4
)

# Identify potential mistakes
# potential_mistakes = []
# for brand_name, merchant_id, product_count in brand_data:
#     if brand_centrality[brand_name] < 0.1 and merchant_centrality[merchant_id] < 0.1:
#         potential_mistakes.append((merchant_id, product_count, brand_name))

# for merchant_id, product_count, brand_name in potential_mistakes:
#     if merchant_id not in mistake_dict:
#         mistake_dict[merchant_id] = []
#     mistake_dict[merchant_id].append(brand_name)

potential_mistake_dict = {}
potential_mistakes = []
for brand_name, merchant_id, product_count in brand_data:
    if int(product_count) < 5:
        merchant_brands = merchant_brand_counts[merchant_id]
        max_brand_count = max(merchant_brands.values())
        # Calculate the relative brand count compared to other brands of the same merchant
        relative_count = brand_counts[brand_name] / max_brand_count
        if relative_count < 0.1:
            # print(merchant_brands, max_brand_count)
            potential_mistakes.append((merchant_id, product_count, brand_name))
        if merchant_id not in potential_mistake_dict:
            potential_mistake_dict[merchant_id] = []
        potential_mistake_dict[merchant_id].append(brand_name)

# exit()
print(len(potential_mistakes))
print(len(potential_mistake_dict))
# Print potential mistakes
# for merchant_id, product_count, brand_name in potential_mistakes:
#     print(
#         f"Merchant ID: {merchant_id}, Product Count: {product_count}, Brand: {brand_name}"
#     )

for merchant_id, brand_names in potential_mistake_dict.items():
    print(f"Merchant {merchant_id} with {len(brand_names)}")
