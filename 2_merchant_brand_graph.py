import networkx as nx
import pandas as pd
from classes.VirtuosoWrapper import VirtuosoWrapper
import matplotlib.pyplot as plt
from pyvis.network import Network


def min_max_normalization(data, column=2):
    min_val = float("inf")
    max_val = float("-inf")
    for row in data:
        value = float(row[column])
        if value < min_val:
            min_val = value
        if value > max_val:
            max_val = value
    normalized_data = []
    for row in data:
        value = float(row[column])
        normalized_value = (value - min_val) / (max_val - min_val)
        normalized_row = row[:2] + [normalized_value] + row[3:]
        normalized_data.append(normalized_row)
    return normalized_data


query = """
SELECT ?brand ?brandName (COUNT(DISTINCT ?product) AS ?productCount) (COUNT(DISTINCT ?productType) AS ?productTypeCount)
WHERE {
  ?brand a <http://omikron44/ontologies/brands> ;
         <http://omikron44/ontologies/brands#brand> ?brandName .
  ?product <http://omikron44/ontologies/products#brand> ?brand ;
           <http://omikron44/ontologies/products#merchant_id> 470 ;
        #    <http://omikron44/ontologies/products#merchant_id> 430 ;
           <http://omikron44/ontologies/products#product_type> ?productType .
}
GROUP BY ?brand ?brandName
"""

virtuoso = VirtuosoWrapper()
merchant_brands_response = virtuoso.get(query)

brand_values = [
    [
        brand_data["brand"]["value"],
        brand_data["brandName"]["value"],
        brand_data["productCount"]["value"],
        brand_data["productTypeCount"]["value"],
    ]
    for brand_data in merchant_brands_response["results"]["bindings"]
]

normalized_data = min_max_normalization(brand_values)

print(brand_values)
G = nx.DiGraph()

G.add_node("merchant_470")
for brand in normalized_data:
    G.add_node(brand[1])  # add brand name as a node
    G.add_edge("merchant_470", brand[1], weight=int(brand[2] * 10))

# nx.draw_circular(G)
# plt.show()

# node_degree = dict(G.degree)
# nx.set_node_attributes(G, node_degree, "size")

net = Network("1000px", "1900px", directed=False, font_color="white", bgcolor="#111111")
net.from_nx(G)
net.show("merchant_brand.html", notebook=False)
