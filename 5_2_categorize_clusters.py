from classes.VirtuosoWrapper import VirtuosoWrapper
import json
import re

def filter_keywords(keywords, title):
    filtered_keywords = []
    title = re.sub(r"[>#+'?$%^*®™()]+|-", "", title)
    title_parts = title.lower().split()
    for keyword in keywords:
      keyword_parts = keyword.split()
      flag = False
      for keyword_part in keyword_parts:
        if keyword_part in title_parts:
          flag=True
          continue
        else:
          flag=False
          break
      if flag:
        filtered_keywords.append(keyword)

    return filtered_keywords


clusters = []

def create_product_category_query(product_uris):
  uri_array = []
  for product_uri in product_uris:
    uri_array.append(f"<{product_uri}>")
  return f"""SELECT DISTINCT ?o
  WHERE{{
  ?product <http://magelon.com/ontologies/products#title> ?product_title .
  ?product <http://magelon.com/ontologies/products#product_type> ?o.
  FILTER(?product IN (
    {",".join(uri_array)}
  ))}}
  """

def update_product_google_categories_query(product_uris,category_uri):
  uri_array = []
  for product_uri in product_uris:
    uri_array.append(f"<{product_uri}>")
  return f"""
      INSERT {{
      ?product <http://omikron44/ontologies/products#google_product_type> <{category_uri}> .
      }}
      WHERE {{
      ?product a <http://omikron44/ontologies/products>.
      FILTER(?product IN (
        {",".join(uri_array)}
      ))
      }}
  """

with open("storage/agglo-clusters.json", "r") as json_file:
  clusters = json.load(json_file)
  
  
virtuoso = VirtuosoWrapper()

categories_query = """
SELECT ?category_uri ?category_name ?full_path
where {
 ?category_uri a <http://magelon.com/ontologies/google_categories>; 
   <http://magelon.com/ontologies/google_categories#full_path> ?full_path;
   rdfs:label ?category_name.
}
"""

attributes_query = """
PREFIX magelon: <http://magelon.com/ontologies/>
SELECT *
where{
 ?attribute a magelon:attributes.
 ?attribute rdfs:label ?attribute_label.
}
"""

categories_result = virtuoso.getAll(categories_query)
category_names = {}
category_paths = {}
for row in categories_result:
    category_paths[row["category_uri"]] = row["full_path"]
    category_names[row["category_uri"]] = row["category_name"]

for i, products in clusters.items():
    product_uris = [product_uri for product_uris in products["product_uris"] for product_uri in product_uris]
    merchant_category_query = create_product_category_query(product_uris=product_uris)
    merchant_categories_result= virtuoso.getAll(merchant_category_query)
    merchant_categories = [row["o"].lower() for row in merchant_categories_result]
    category_keywords = []
    for merchant_category in merchant_categories:
      category_keywords.extend(re.findall(r"\b(\w+-?\w+)\b", merchant_category))
    print(set(category_keywords))
    category_scores = []
    for uri,name in category_names.items():
        category_words = name.split()
        category_score = 0
        for category_word in category_words:
            if(category_word.lower() in " ".join(category_keywords).lower()):
                category_score +=len(category_word)/len(name)
        category_scores.append((category_score, name,uri))
    top_categories = sorted(category_scores, key=lambda x: x[0], reverse=True)
    print("\n")
    for text in products["product_titles"][0:3]:
        print("Products to receive categories")
        print(text)
    print("\n")
    print("Category matches")
    for i,text in enumerate(top_categories[0:5]):
        print("\n")
        print(f"{i}:{text[1]}:({category_paths[text[2]]})")
    print("\n")
    selection = input("Check paths and assign if relation is found[0-4]")
    if(selection != "" and int(selection) in range(0,4)):
      print(f"selection {top_categories[int(selection)]}")
      query = update_product_google_categories_query(
        product_uris,
        top_categories[int(selection)][2]
      )
      print(query)
      exit()
      # virtuoso.save(query)
      #update product google categories
    else:
      print("no selection")


for i, products in clusters.items():
    category_scores = []
    cluster_keywords = []
    for product in products["product_titles"]:
        cluster_keywords.extend(re.findall(r"\b(\w+-?\w+)\b", product))
    for uri,name in category_names.items():
        category_words = name.split()
        category_score = 0
        for category_word in category_words:
            if(category_word.lower() in " ".join(cluster_keywords).lower()):
                category_score +=len(category_word)/len(name)
        category_scores.append((category_score, name,uri))
    top_categories = sorted(category_scores, key=lambda x: x[0], reverse=True)
    for text in products["product_titles"][0:3]:
        print(text)
    for text in top_categories[0:5]:
        print(text[1])
    input("Check paths and assign if relation is found")
# for each cluster find words that relates the products to a category


for attribute in attributes:
    if attribute in category_names:
        print(attribute)

matching_categories = {}

# Create a regex pattern to match any string in the first array
for attribute in attributes:
    if len(attribute.split()) > 1:
        pattern = "|".join(map(re.escape, attribute.split()))
    else:
        pattern = attribute
    # Combine the pattern using the '|' (OR) operator
    regex = re.compile(pattern)
    # Check if any category in the second array matches the regex pattern
    matches = [category for category in category_names if regex.search(category)]
    if len(matches) > 0:
        matching_categories[attribute] = matches
