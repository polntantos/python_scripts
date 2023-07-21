import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from classes.VirtuosoWrapper import VirtuosoWrapper
import json

# Step 1: Tokenization
def tokenize(title):
    tokens = re.findall(r'\b\w+\b', title)
    return tokens

# Step 2: Preprocessing
def preprocess(tokens, specific_cases=None):
    if specific_cases is None:
        specific_cases = {}

    # Convert tokens to lowercase
    tokens = [token.lower() for token in tokens]

    # Handle specific cases
    for case in specific_cases:
        tokens = [re.sub(case, specific_cases[case], token) for token in tokens]

    return tokens

# Step 3: Frequency analysis
def get_token_frequencies(titles):
    all_tokens = [token for title in titles for token in title]
    token_frequencies = Counter(all_tokens)
    return token_frequencies

# Step 4: Identify combinations
def identify_combinations(titles, min_occurrences=2, ngram_length=2):
    combinations = []
    for title in titles:
        tokens = preprocess(tokenize(title))
        for i in range(len(tokens) - ngram_length + 1):
            ngram = ' '.join(tokens[i:i+ngram_length])
            if titles.count(title) >= min_occurrences:
                combinations.append(ngram)
    return combinations

# Step 5: TF-IDF vectorization
def perform_tfidf_vectorization(titles):
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(titles)
    feature_names = tfidf_vectorizer.get_feature_names_out()
    return tfidf_matrix, feature_names

# Step 6: Entity recognition with Spacy
def perform_entity_recognition(titles):
    nlp = spacy.load('en_core_web_sm')
    entities = set()  # Use a set to eliminate duplicates
    for title in titles:
        doc = nlp(title)
        entities.update([ent.text for ent in doc.ents])
    return list(entities)

# Step 7: Assign extracted entities to titles
def assign_entities_to_titles(titles, entities):
    nlp = spacy.load('en_core_web_sm')
    for title in titles:
        doc = nlp(title['title'])
        title['entities'] = [entity for entity in entities if entity in doc.text]
    return titles

virtuoso = VirtuosoWrapper()
brands = []
offset = 0

while True:
  response=brand_query = f"""
  SELECT ?brand
  WHERE{{
    ?brand a <http://omikron44/ontologies/brands>.
  }} GROUP BY ?brand
  OFFSET {offset}
  LIMIT 10000
  """
  
  response = virtuoso.get(brand_query)
  brands.extend(response)
  offset += len(response)
  if len(response)<10000:
    break

# print(brands)
# print(len(brands))
# exit()
while True:
  query = f"""
  SELECT ?s ?title
    WHERE {{
      ?s a <http://omikron44/ontologies/products>.
      ?s <http://omikron44/ontologies/products#title> ?title.
  }}
  ORDER BY ?s
  OFFSET {offset}
  LIMIT 10000 
  """

  response = virtuoso.get(query)

  product_items = []
  for row in response["results"]["bindings"]:
    product_items.append({'id':row['s']['value'],'title':row['title']['value']})

product_titles = [product['title'] for product in product_items]

# Step 1: Tokenization
tokenized_titles = [tokenize(title) for title in product_titles]

# Step 2: Preprocessing
specific_cases = {
    'colour': 'color',
    'specific_case': 'replacement'
}
preprocessed_titles = [preprocess(tokens, specific_cases) for tokens in tokenized_titles]

# Step 3: Frequency analysis
token_frequencies = get_token_frequencies(preprocessed_titles)

# Step 4: Identify combinations
combinations = identify_combinations(product_titles, min_occurrences=2, ngram_length=2)

# Step 5: TF-IDF vectorization
tfidf_matrix, feature_names = perform_tfidf_vectorization(product_titles)

# Step 6: Entity recognition with Spacy
entities = perform_entity_recognition(product_titles)

# Example usage
product_titles_with_entities = assign_entities_to_titles(product_items, entities)

# Print the results
print("Combinations:")
print(combinations)
print("Token Frequencies:")
print(token_frequencies)
# print("TF-IDF Matrix:")
# print(tfidf_matrix.toarray())
print("Feature Names:")
print(feature_names)
print("Entities:")
print(entities)

# Convert the list of titles with entities to a dictionary
titles_dict = {'titles': product_titles_with_entities}

# Save the dictionary as JSON
with open('titles_with_entities.json', 'w') as json_file:
    json.dump(titles_dict, json_file, indent=4)

# # Print the updated list of titles with assigned entities
# for title in product_titles_with_entities:
#     print(f"Title ID: {title['id']}")
#     print(f"Title: {title['title']}")
#     print(f"Entities: {title['entities']}")
#     print()