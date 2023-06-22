import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from classes.VirtuosoWrapper import VirtuosoWrapper

query = """
SELECT ?merchant_id (COUNT(DISTINCT ?brand) AS ?brandCount) (COUNT(DISTINCT ?product) AS ?productCount)
WHERE {
  ?merchant a <http://omikron44/ontologies/merchants> ;
           <http://omikron44/ontologies/merchants#id> ?merchant_id .
  ?product <http://omikron44/ontologies/products#merchant_id> ?merchant_id ;
           <http://omikron44/ontologies/products#brand> ?brand .
}
GROUP BY ?merchant_id
"""
virtuoso = VirtuosoWrapper()
query_response = virtuoso.get(query)

# data = []
merchant_ids = []
brand_counts = []
product_counts = []
for row in query_response["results"]["bindings"]:
    merchant_ids.append(row["merchant_id"]["value"])
    brand_counts.append(int(row["brandCount"]["value"]))
    product_counts.append(int(row["productCount"]["value"]))

    # data.append(
    #     [
    #         row["merchant_id"]["value"],
    #         row["brandCount"]["value"],
    #         row["productCount"]["value"],
    #     ]
    # )

# Extract merchant brand counts and product counts
# merchant_data = np.array([[float(row[1]), float(row[2])] for row in data])

# scaler = StandardScaler()
# normalized_data = scaler.fit_transform(merchant_data)

max_value = max(max(brand_counts), max(product_counts))
normalized_brand_counts = [count / max_value for count in brand_counts]
normalized_product_counts = [count / max_value for count in product_counts]
# Perform clustering using DBSCAN
normalized_data = np.column_stack((normalized_brand_counts, normalized_product_counts))
dbscan = DBSCAN(eps=0.2, min_samples=5)
clusters = dbscan.fit_predict(normalized_data)

# Print the cluster labels
print("Cluster labels:")
for merchant, label in zip([row for row in merchant_ids], clusters):
    print(f"{merchant}: {label}")

# Plot the clusters
unique_labels = set(clusters)
colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]

for k, col in zip(unique_labels, colors):
    if k == -1:
        # Outliers are plotted in black
        col = [0, 0, 0, 1]

    class_members = [index[0] for index in np.argwhere(clusters == k)]
    cluster_data = normalized_data[class_members]
    plt.scatter(
        cluster_data[:, 0],
        cluster_data[:, 1],
        c=[col],
        marker="o",
        s=100,
        edgecolor="k",
    )

max_prod_count = max(normalized_data[:, 1])

plt.xlabel("Brand Counts")
plt.ylabel("Product Counts")
plt.title("DBSCAN Clustering")
plt.plot([0, max_prod_count], [0, max_prod_count], color="red", linestyle="--")
plt.show()
