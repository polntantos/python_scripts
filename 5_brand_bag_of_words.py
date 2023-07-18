from classes.VirtuosoWrapper import VirtuosoWrapper
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

query = """SELECT ?product_title
WHERE {
  ?product <http://magelon.com/ontologies/products#brand> ?brand_uri ;
           <http://magelon.com/ontologies/products#title> ?product_title .
  {
    SELECT ?brand_uri
    WHERE {
      {
        ?brand_uri ?p "Bosch" ;
                   <http://magelon.com/ontologies/brands#brand> ?brand_name ;
                   a <http://magelon.com/ontologies/brands> .
      }
      UNION
      {
        ?b ?n "Bosch" ;
           ?refers ?brand_uri ;
           <http://magelon.com/ontologies/brands#brand> ?brand_name ;
           a <http://magelon.com/ontologies/brands> .
      }
    }
  }
}"""

virtuoso = VirtuosoWrapper()
product_titles =[row['product_title'] for row in virtuoso.getAll(query)]

vectorizer1 = TfidfVectorizer(stop_words="english",ngram_range=(1,1),min_df=1,max_df=0.5) # to catch product sku
vectorizer2 = TfidfVectorizer(stop_words="english",ngram_range=(2,2),min_df=2,max_df=0.5)
vectorizer3 = TfidfVectorizer(stop_words="english",ngram_range=(3,3),min_df=2,max_df=0.5)

X1=vectorizer1.fit_transform(product_titles)
X2=vectorizer2.fit_transform(product_titles)
X3=vectorizer3.fit_transform(product_titles)

# tf_idf_vectors = vectorizer.transform(product_titles)

# Print the TF-IDF vectors
# print(tf_idf_vectors)
input("Press any key to continue...")

vocab1 = vectorizer1.vocabulary_

vocab = sorted(vocab1.items(),key=lambda x:x[1],reverse=True)

feature_values = [i[0] for i in vocab]
for value, seen in vocab:
  for value2, seen in vocab:
    if value2 != value and value2 in value:
      if(value2 in feature_values):
        feature_values.pop(feature_values.index(value2))