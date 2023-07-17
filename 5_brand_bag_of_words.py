from classes.VirtuosoWrapper import VirtuosoWrapper
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

query = """SELECT ?product_title
WHERE {
  ?product <http://omikron44/ontologies/products#brand> ?brand_uri ;
           <http://omikron44/ontologies/products#title> ?product_title .
  {
    SELECT ?brand_uri
    WHERE {
      {
        ?brand_uri ?p "Bosch" ;
                   <http://omikron44/ontologies/brands#brand> ?brand_name ;
                   a <http://omikron44/ontologies/brands> .
      }
      UNION
      {
        ?b ?n "Bosch" ;
           ?refers ?brand_uri ;
           <http://omikron44/ontologies/brands#brand> ?brand_name ;
           a <http://omikron44/ontologies/brands> .
      }
    }
  }
}"""

virtuoso = VirtuosoWrapper()
product_titles =[row['product_title'] for row in virtuoso.getAll(query)]

vectorizer = TfidfVectorizer(stop_words="english",ngram_range=(1,3),min_df=5,max_df=0.8)

vectorizer.fit(product_titles)

tf_idf_vectors = vectorizer.transform(product_titles)

# Print the TF-IDF vectors
print(tf_idf_vectors)
input("Press any key to continue...")

vocab = vectorizer.vocabulary_
vocab = sorted(vocab.items(),key=lambda x:x[1],reverse=True)

feature_values = [i[0] for i in vocab]
for value, seen in vocab:
  for value2, seen in vocab:
    if value2 != value and value2 in value:
      if(value2 in feature_values):
        feature_values.pop(feature_values.index(value2))