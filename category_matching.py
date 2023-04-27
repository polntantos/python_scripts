import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load the merchant and Google categories into a pandas dataframe
categories_df = pd.read_csv('categories.csv')

# Preprocess the category names
categories_df['merchant_category'] = categories_df['merchant_category'].str.lower().str.replace('[^\w\s]', '').str.split()
categories_df['google_category'] = categories_df['google_category'].str.lower().str.replace('[^\w\s]', '').str.split()

# Vectorize the category names using TF-IDF
vectorizer = TfidfVectorizer()
merchant_category_vectors = vectorizer.fit_transform(categories_df['merchant_category'].apply(lambda x: ' '.join(x)))
google_category_vectors = vectorizer.transform(categories_df['google_category'].apply(lambda x: ' '.join(x)))

# Compute the cosine similarity between each pair of merchant and Google categories
cosine_similarities = cosine_similarity(merchant_category_vectors, google_category_vectors)

# Find the best matching Google category for each merchant category
best_matches = cosine_similarities.argmax(axis=1)
mapped_categories = pd.DataFrame({'merchant_category': categories_df['merchant_category'],
                                  'google_category': categories_df['google_category'].iloc[best_matches]})