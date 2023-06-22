import networkx as nx
import matplotlib.pyplot as plt
from classes.VirtuosoWrapper import VirtuosoWrapper

query = """
SELECT ?brand ?brandName ?merchantId (COUNT(DISTINCT ?product) AS ?productCount) (COUNT(DISTINCT ?productType) AS ?productTypeCount)
WHERE {
  ?brand a <http://omikron44/ontologies/brands> ;
         <http://omikron44/ontologies/brands#brand> ?brandName .
  ?product <http://omikron44/ontologies/products#brand> ?brand ;
           <http://omikron44/ontologies/products#merchant_id> ?merchantId ;
           <http://omikron44/ontologies/products#product_type> ?productType .
}
GROUP BY ?brand ?brandName ?merchantId

"""
virtuoso = VirtuosoWrapper()
query_response = virtuoso.get(query)

data = []
for row in query_response["results"]["bindings"]:
    data.append(
        [
            row["brand"]["value"],
            row["brandName"]["value"],
            row["merchantId"]["value"],
            row["productCount"]["value"],
            # row["productTypeCount"]["value"],
        ]
    )

# Create an empty graph
graph = nx.Graph()

# Define dictionaries to store brand appearance counts
brand_product_counts = {}
brand_product_type_counts = {}

# Iterate through the data and add nodes and edges to the graph
for row in data:
    # brand, brand_name, merchant_id, product_count, product_type_count = row
    brand, brand_name, merchant_id, product_count = row
    graph.add_node(brand, label=brand_name)
    graph.add_node(merchant_id)
    graph.add_edge(
        brand,
        merchant_id,
        product_count=product_count,
        # product_type_count=product_type_count,
    )

    # Update brand appearance counts
    if brand not in brand_product_counts:
        brand_product_counts[brand] = product_count
    else:
        brand_product_counts[brand] += product_count

    # if brand not in brand_product_type_counts:
    #     brand_product_type_counts[brand] = product_type_count
    # else:
    #     brand_product_type_counts[brand] += product_type_count

# Set node positions for better visualization
pos = nx.spring_layout(graph)

# Draw nodes
brand_nodes = [node for node in graph.nodes if "label" in graph.nodes[node]]
merchant_nodes = [node for node in graph.nodes if node not in brand_nodes]

nx.draw_networkx_nodes(graph, pos, nodelist=brand_nodes, node_color="b", label="Brands")
nx.draw_networkx_nodes(
    graph, pos, nodelist=merchant_nodes, node_color="r", label="Merchants"
)

# Draw edges
nx.draw_networkx_edges(graph, pos)

# Draw node labels
brand_labels = nx.get_node_attributes(graph, "label")
nx.draw_networkx_labels(graph, pos, labels=brand_labels)

# Draw edge labels
product_count_labels = nx.get_edge_attributes(graph, "product_count")
# product_type_count_labels = nx.get_edge_attributes(graph, "product_type_count")
nx.draw_networkx_edge_labels(
    graph, pos, edge_labels=product_count_labels, label_pos=0.4
)
# nx.draw_networkx_edge_labels(
#     graph, pos, edge_labels=product_type_count_labels, label_pos=0.6
# )

# Add legend
plt.legend()

# Calculate brand performance metrics
low_performer_merchants = []
high_performer_merchants = []

for brand in brand_nodes:
    merchant_counts = sum([1 for edge in graph.edges(brand) if edge[0] == brand])
    if merchant_counts == 1:
        low_performer_merchants.append(list(graph.edges(brand))[0][1])
    else:
        high_performer_merchants.extend(
            [edge[1] for edge in graph.edges(brand) if edge[0] == brand]
        )

print("Merchants with mostly low-performing brands:", low_performer_merchants)

# Show the graph
plt.axis("off")
plt.show()
