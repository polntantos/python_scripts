from classes.VirtuosoWrapper import VirtuosoWrapper
import json
import re
from rdflib import Graph, URIRef


def filter_keywords(keywords, title):
    filtered_keywords = []
    title = re.sub(r"[>#+'?$%^*®™()]+|-", "", title)
    title_parts = title.lower().split()
    for keyword in keywords:
        keyword_parts = keyword.split()
        flag = False
        for keyword_part in keyword_parts:
            if keyword_part in title_parts:
                flag = True
                continue
            else:
                flag = False
                break
        if flag:
            filtered_keywords.append(keyword)

    return filtered_keywords


clusters = []
# contract 543513
# cartridges 356


def create_product_category_query(product_uris):
    uri_array = []
    for product_uri in product_uris:
        uri_array.append(f"<{product_uri}>")
        if len(uri_array) > 1000:
            break
    return f"""SELECT DISTINCT ?o
  WHERE{{
  ?product <http://magelon.com/ontologies/products#title> ?product_title .
  ?product <http://magelon.com/ontologies/products#product_type> ?o.
  FILTER(?product IN (
    {",".join(uri_array)}
  ))}}
  """


def update_product_google_categories_query(product_uris, category_uri):
    uri_array = []
    rdf_graph = Graph()
    for product_uri in product_uris:
        # uri_array.append(f"<{product_uri}>")
        rdf_graph.add(
            (
                URIRef(product_uri),
                URIRef("http://magelon.com/ontologies/products#google_product_type"),
                URIRef(category_uri),
            )
        )

    return rdf_graph


#     return f"""
#       INSERT {{
#       ?product <http://magelon.com/ontologies/products#google_product_type> <{category_uri}> .
#       }}
#       WHERE {{
#       ?product a <http://magelon.com/ontologies/products>.
#       FILTER(?product IN (
#         {",".join(uri_array)}
#       ))
#       }}
#   """


def get_category_score(category_name, category_keywords):
    category_words = category_name.split()
    category_score = 0
    for category_word in category_words:
        if category_word.lower() in " ".join(category_keywords).lower():
            category_score += len(category_word) / len(name)
    return category_score


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

categories_result = virtuoso.getAll(categories_query)
category_names = {}
category_paths = {}
for row in categories_result:
    category_paths[row["category_uri"]] = row["full_path"]
    category_names[row["category_uri"]] = row["category_name"]

remaining_clusters = {}

for index, products in clusters.items():
    product_uris = [
        product_uri
        for product_uris in products["product_uris"]
        for product_uri in product_uris
    ]
    merchant_category_query = create_product_category_query(product_uris=product_uris)
    merchant_categories_result = virtuoso.getAll(merchant_category_query)
    merchant_categories = [row["o"].lower() for row in merchant_categories_result]
    category_keywords = []
    for merchant_category in merchant_categories:
        category_keywords.extend(re.findall(r"\b(\w+-?\w+)\b", merchant_category))
    print(set(category_keywords))
    category_scores = []
    for uri, name in category_names.items():
        category_score = get_category_score(name, category_keywords)
        category_scores.append((category_score, name, uri))
    top_categories = sorted(category_scores, key=lambda x: x[0], reverse=True)
    print("\n")
    print("Products to receive categories")
    for text in products["product_titles"][0:3]:
        print(text)
    print("\n")
    print("Category matches")
    for i, text in enumerate(top_categories[0:5]):
        print("\n")
        print(f"{i}:{text[1]}:({category_paths[text[2]]})")
    print("\n")
    selection = input("Check paths and assign if relation is found[0-4]")
    if selection != "" and int(selection) in range(0, 5):
        print(f"selection {top_categories[int(selection)]}")
        # split in batches

        graph = update_product_google_categories_query(
            product_uris, top_categories[int(selection)][2]
        )
        # print(query)
        # update product google categories
        virtuoso.save(graph)
        continue
    else:
        print("no selection")
    for uri, name in category_paths.items():  # test for whole paths
        category_score = get_category_score(name, category_keywords)
        category_scores.append((category_score, name, uri))
    top_categories = sorted(category_scores, key=lambda x: x[0], reverse=True)
    print("\n")
    print("Products to receive categories")
    for text in products["product_titles"][0:3]:
        print(text)
    print("\n")
    print("Category matches")
    for i, text in enumerate(top_categories[0:5]):
        print("\n")
        print(f"{i}:{text[1]}:({category_paths[text[2]]})")
    print("\n")
    selection = input("Check paths and assign if relation is found[0-4]")
    if selection != "" and int(selection) in range(0, 5):
        print(f"selection {top_categories[int(selection)]}")
        graph = update_product_google_categories_query(
            product_uris, top_categories[int(selection)][2]
        )
        # print(query)
        virtuoso.save(graph)
        # update product google categories
        continue
        # exit()
    else:
        print("no selection")
    remaining_clusters[index] = products

print("Remaining clusters")
print(remaining_clusters)
print("Manual phase")
# Custom category assignment
for index, products in remaining_clusters.items():
    product_uris = [
        product_uri
        for product_uris in products["product_uris"]
        for product_uri in product_uris
    ]
    print("Products to receive categories")
    for text in products["product_titles"][0:3]:
        print(text)
    print("\n")
    category_id = input(
        "Give the id of the google category from the txt file for assignment(ID - Category > Path)"
    )
    if category_id != "":
        category_uri = (
            f"http://magelon.com/ontologies/google_categories/id={category_id}"
        )
        graph = update_product_google_categories_query(product_uris, category_uri)
        virtuoso.save(graph)
