#pip install pymysql

from sklearn.feature_extraction.text import CountVectorizer
import pymysql
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

conn = pymysql.connect(host='192.168.1.2', user='root', password='password', database='test')

query="""
SELECT title from products limit 10000
"""

cursor = conn.cursor()
cursor.execute(query)


title_array=[]
for row in cursor:
    title_array.append(row[0])

def elbow_method():
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(title_array)

    # Set the range of k values to test
    k_range = range(1, 11)

    # Initialize an empty list to store the WCSS values for each k
    wcss = []

    # Compute the WCSS for each k
    for k in k_range:
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(X)
        wcss.append(kmeans.inertia_)

    # Plot the results
    plt.plot(k_range, wcss)
    plt.xlabel('Number of clusters')
    plt.ylabel('Within-cluster sum of squares')
    plt.title('Elbow method for optimal k')
    plt.show()


def extract_features(texts, n_clusters=5):
    # Convert the input texts to a Bag-of-Words representation
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(texts)

    # Cluster the input texts using K-Means
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(X)

    # Extract the most frequent words or phrases in each cluster
    features = []
    for i in range(n_clusters):
        cluster_center = kmeans.cluster_centers_[i]
        top_features_idx = cluster_center.argsort()[::-1][:5]
        top_features = [vectorizer.get_feature_names_out()[idx] for idx in top_features_idx]
        features.extend(top_features)

    # Remove duplicate features
    features = list(set(features))

    # Create the output array
    output = []
    for text in texts:
        text_features = []
        for feature in features:
            if feature in text:
                text_features.append(feature)
        output.append(text_features)

    return output

output_bag=extract_features(title_array[:10])

def extract_features_tfidf(product_titles):
    # Initialize the TF-IDF vectorizer
    tfidf = TfidfVectorizer()

    # Fit the vectorizer to the list of product titles
    tfidf.fit(product_titles)

    # Transform the product titles to a TF-IDF bag-of-words matrix
    features = tfidf.transform(product_titles)

    # Get the feature names (i.e., the words in the vocabulary)
    feature_names = tfidf.get_feature_names_out()

    # Convert the feature matrix to a sparse array for efficiency
    features = features.toarray()

    return features, feature_names

output_bag=extract_features_tfidf(title_array) #tfidf is more promising  