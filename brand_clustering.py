import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from classes.VirtuosoWrapper import VirtuosoWrapper
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import json

virtuoso = VirtuosoWrapper()
offset = 0
data = []
while True:
    print(f"running with offset {offset}")
    query = f"""
    SELECT ?brand ?brandTitle (COUNT(DISTINCT ?product) AS ?productCount) (COUNT(DISTINCT ?productType) AS ?productTypeCount) (COUNT(DISTINCT ?merchant) AS ?merchantCount) (GROUP_CONCAT(DISTINCT ?merchant; separator=", ") AS ?merchantIds)
    WHERE {{
    ?brand a <http://omikron44/ontologies/brands> ;
            <http://omikron44/ontologies/brands#brand> ?brandTitle .
    ?product <http://omikron44/ontologies/products#brand> ?brand .
    ?product <http://omikron44/ontologies/products#merchant_id> ?merchant;
                    <http://omikron44/ontologies/products#title> ?title;
                    <http://omikron44/ontologies/products#product_type> ?productType.
        FILTER (?brand != <http://omikron44/ontologies/brands/id=>)
    }}GROUP BY ?brand ?brandTitle
    offset {offset} limit 10000
    """
    brand_data_query = virtuoso.get(query)
    query_brand_rows = [brand for brand in brand_data_query["results"]["bindings"]]
    all_query_labels = [
        "brand",
        "brandTitle",
        "productCount",
        "productTypeCount",
        "merchantCount",
        "merchantIds",
    ]
    brand_result_array = [
        [brand_row[label]["value"] for label in all_query_labels]
        for brand_row in query_brand_rows
    ]
    data.extend(brand_result_array)
    if len(query_brand_rows) < 10000:
        break
    offset = len(data)

# Parse data into separate lists
brandUris = []
brands = []
product_count = []
category_count = []
merchant_count = []
merchant_ids = []

for row in data:
    brandUris.append(row[0])
    brands.append(row[1])
    product_count.append(int(row[2]))
    category_count.append(int(row[3]))
    merchant_count.append(int(row[4]))
    merchant_ids.append(row[5])

# Convert features to a numerical format
X = pd.DataFrame(
    {
        # "ProductCount": product_count,
        "CategoryCount": category_count,
        "MerchantCount": merchant_count,
    }
)

# Scale the numerical features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Apply clustering algorithm (e.g., DBSCAN)
# dbscan = DBSCAN(eps=0.00035, min_samples=50)  ##min eps tested successfully 0.0004 for product_counts
dbscan = DBSCAN(
    eps=0.00035, min_samples=10
)  ##min eps tested successfully 0.0004 for category counts
labels = dbscan.fit_predict(X_scaled)

# Analyze clustering results
clusters = set(labels)

cluster_results = {}

for cluster in clusters:
    cluster_indices = labels == cluster
    cluster_brands = [brands[i] for i, value in enumerate(cluster_indices) if value]
    # print(f"Cluster {cluster}: {cluster_brands}")
    cluster_results[int(cluster)] = cluster_brands


# Save results to a JSON file
output_file = "clusters/brand_clusters.json"

with open(output_file, "w") as f:
    json.dump(cluster_results, f)

print(f"Clustering results saved to {output_file}.")

# Count the number of brands in each cluster
cluster_counts = {cluster: len(brands) for cluster, brands in cluster_results.items()}

# Create a bar plot of cluster counts
plt.bar(cluster_counts.keys(), cluster_counts.values())
plt.xlabel("Cluster")
plt.ylabel("Brand Count")

# Adjust the y-axis scale
plt.ylim(bottom=0, top=max(cluster_counts.values()) * 1.1)

plt.title("Cluster Distribution")
plt.show()

# Create a matrix to represent the presence of brands in each cluster
cluster_matrix = np.zeros((len(brands), len(cluster_results)))
brand_indices = {brand: i for i, brand in enumerate(brands)}

for cluster, cluster_brands in cluster_results.items():
    for brand in cluster_brands:
        brand_index = brand_indices[brand]
        cluster_matrix[brand_index, cluster] = 1

# Transpose the cluster matrix
cluster_matrix_transposed = cluster_matrix.T

# Create a heatmap
sns.heatmap(cluster_matrix_transposed, cmap="coolwarm", cbar=False)
plt.xlabel("Brand")
plt.ylabel("Cluster")
plt.title("Cluster Heatmap")
plt.show()


# we have identified the cluster #2 as the one containing faulty and no usefull brands
minimum = min(clusters)
maximum = max(clusters)
suspect_cluster = input(
    f"Can you provide the cluster that you think has the most faulty brands? (Insert number between {minimum}-{maximum}) : "
)

# Initialize lists to store faulty and non-faulty data
faulty_brands = []
non_faulty_brands = []


# Iterate over the clusters
for cluster_label, cluster_brands in cluster_results.items():
    print(cluster_label, type(cluster_label))
    if cluster_label == int(suspect_cluster):
        print(f"cluster_label=={suspect_cluster}")
        faulty_brands.extend(cluster_brands)
    else:
        # print("cluster_label!=2")
        non_faulty_brands.extend(cluster_brands)


faulty_brand_data = [
    {
        "brand": brandUris[brands.index(brand)],
        "brand_name": brand,
        "merchant": merchant_ids[brands.index(brand)],
    }
    for brand in faulty_brands
]

print(faulty_brand_data)

# Save results to a JSON file
faulty_brand = "clusters/product_types_faulty_brand_data.json"
# faulty_brand = "clusters/products_faulty_brand_data.json"

with open(faulty_brand, "w") as f:
    json.dump(faulty_brand_data, f)

print(f"Clustering results saved to {faulty_brand}.")

# Extract the data for the scatter plot
# product_count
# x_faulty = [int(product_count[brands.index(brand)]) for brand in faulty_brands]
# x_non_faulty = [int(product_count[brands.index(brand)]) for brand in non_faulty_brands]

# category_count
x_faulty = [int(category_count[brands.index(brand)]) for brand in faulty_brands]
x_non_faulty = [int(category_count[brands.index(brand)]) for brand in non_faulty_brands]

y_faulty = [int(merchant_count[brands.index(brand)]) for brand in faulty_brands]
y_non_faulty = [int(merchant_count[brands.index(brand)]) for brand in non_faulty_brands]

# Create the scatter plot
plt.scatter(
    x_non_faulty, y_non_faulty, label=f"Non-Faulty Brand ({len(non_faulty_brands)})"
)
plt.scatter(
    x_faulty, y_faulty, label=f"Faulty Brands ({len(faulty_brands)})", color="red"
)

# Set labels and title
plt.xlabel("Number of Products")
plt.ylabel("Number of Merchants")
plt.title("Scatter Plot of Faulty and Non-Faulty Brands")

# Add a legend
plt.legend()

# Display the plot
plt.show()
