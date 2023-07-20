from classes.VirtuosoWrapper import VirtuosoWrapper
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import re
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")

color_query = """
select ?color_uri ?label
where { 
{?color_uri a <http://magelon.com/ontologies/colors>.}
UNION
{?color_uri a <http://omikron44/ontologies/mixture_colors>.}
UNION
{?color_uri a <http://magelon.com/ontologies/color_variations>.}
?color_uri <http://www.w3.org/2000/01/rdf-schema#label> ?label.
}
"""

brand_name = "Bosch"
query = """
SELECT ?product_title ?mpn ?merchant_id
WHERE {
  ?product <http://magelon.com/ontologies/products#brand> ?brand_uri ;
           <http://magelon.com/ontologies/products#title> ?product_title .
           ?product <http://magelon.com/ontologies/products#mpn> ?mpn.
           OPTIONAL{?product <http://magelon.com/ontologies/products#merchant_id> ?merchant_id }
  {
    Select ?brand_uri ?brand_name
    WHERE {
      {
      ?brand_uri ?p "Bosch".
      ?brand_uri <http://magelon.com/ontologies/brands#brand> ?brand_name.
      ?brand_uri a <http://magelon.com/ontologies/brands>.
      }
      UNION
      {
      ?b ?n "Bosch".
      ?brand_uri ?refers ?b.
      ?brand_uri <http://magelon.com/ontologies/brands#brand> ?brand_name.
      ?brand_uri a <http://magelon.com/ontologies/brands>.
      }
    }
  }
}
"""

virtuoso = VirtuosoWrapper()
response = virtuoso.getAll(query)
product_titles = [row["product_title"] for row in response]
mpns = set([row["mpn"] for row in response])
response_colors = virtuoso.getAll(color_query)
colors = set([row["label"] for row in response_colors])
stopwords_list = stopwords.words("english")
stopwords_list.extend([brand_name, brand_name.lower()])
stopwords_list.extend(map(lambda x: x.lower(), mpns))
stopwords_list.extend(map(lambda x: x.lower(), colors))

vectorizer = TfidfVectorizer(
    stop_words=stopwords_list, ngram_range=(1, 2), min_df=1, max_df=0.5
)

# vectorizer1 = TfidfVectorizer(
#     stop_words="english", ngram_range=(1, 1), min_df=1, max_df=0.5
# )  # to catch product sku
# vectorizer2 = TfidfVectorizer(
#     stop_words="english", ngram_range=(2, 2), min_df=2, max_df=0.5
# )
# vectorizer3 = TfidfVectorizer(
#     stop_words="english", ngram_range=(3, 3), min_df=2, max_df=0.5
# )

X = vectorizer.fit_transform(product_titles)

# X1 = vectorizer1.fit_transform(product_titles)
# X2 = vectorizer2.fit_transform(product_titles)
# X3 = vectorizer3.fit_transform(product_titles)

# tf_idf_vectors = vectorizer.transform(product_titles)

# Print the TF-IDF vectors
# print(tf_idf_vectors)
input("Press any key to continue...")

vocab = [word for word in vectorizer.vocabulary_]

# assign colors and mpns to products by checking their titles in rdf.Graph
sand_words = [word for word in vocab if "sand" in word]

# You now have features to assign to products
# You have named features (brand,color,mpn)
# You have unknown features (
# 'battery 334', '334 year'
# 'plus sanding', 'sanding sh'
# ) etc

# now we need to make a graph out of everything
# assign values as
# ?product <http://magelon.com/ontologies/has_attribute#value_type> <http://magelon.com/ontologies/attribute/value>;
# a <http://magelon.com/ontologies/attribute_type>.
# ?product <http://magelon.com/ontologies/has_attribute#brand> <http://magelon.com/ontologies/attribute/Bosch>;
# a <http://magelon.com/ontologies/brand>.
# maybe we can reason with that (whatever reason is)
# maybe same attribute products show their category by grouping together
# maybe categories find a word to word match in the attributes and help us assign them
