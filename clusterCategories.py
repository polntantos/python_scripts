import json
import pymysql
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from rdflib import Graph, URIRef, Literal, BNode, Namespace, RDF, RDFS
import matplotlib.pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage

# Connect to MySQL database
def connect_to_database():
    return pymysql.connect(
        host='192.168.10.30',
        user='homestead',
        password='secret',
        db='homestead'
    )

def get_distinct_categories(cursor):
    print('Getting categories')
    cursor.execute("SELECT DISTINCT x.product_type FROM homestead.products x WHERE x.product_type NOT LIKE '\"\"' OR x.product_type IS NOT NULL")
    return [row[0] for row in cursor.fetchall()]

def perform_agglomerative_clusterring(categories):
    print('Clustering categories')
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(categories)
    # Z = linkage(X.toarray(), 'ward')
    
    # plt.figure(figsize=(25, 10))
    # dendrogram(Z)
    # plt.show()

    clustering = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=2, 
        linkage='ward',
    )
    
    cluster_labels = clustering.fit_predict(X.toarray())
    clusters = {}
    
    for i, cluster_label in enumerate(cluster_labels):
        if cluster_label not in clusters:
            clusters[cluster_label.item()] = []
        clusters[cluster_label.item()].append(categories[i])

    print(clusters)
    return clusters

def main():
    db = connect_to_database()
    cursor = db.cursor()
    categories = get_distinct_categories(cursor)
    clusters = perform_agglomerative_clusterring(categories)
    with open(f"clusters/category-clusters.json","w") as f:
        myKeys = list(clusters.keys())
        myKeys.sort()
        sorted_dict = {i: clusters[i] for i in myKeys}
        json.dump(sorted_dict,f)
main()