import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering

# Step 1: Fetch the product titles and IDs from Virtuoso
# Assuming you have two lists: titles and ids

# Step 2: Preprocess the data

# Step 3: Vectorize the data
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(titles)

# Step 4: Perform clustering
clusterer = AgglomerativeClustering(
    n_clusters=None, distance_threshold=0.7, linkage="ward"
)
cluster_labels = clusterer.fit_predict(X.toarray())

# Step 5: Group the titles and IDs by cluster label
clusters = {}
for i, label in enumerate(cluster_labels):
    if label not in clusters:
        clusters[label] = []
    clusters[label].append({"title": titles[i], "id": ids[i]})

# Step 6: Dump the clusters in JSON format
with open("clusters.json", "w") as f:
    json.dump(clusters, f, indent=4)
