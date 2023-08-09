import json
import spacy
from classes.VirtuosoWrapper import VirtuosoWrapper
from sklearn.metrics import jaccard_score

virtuoso = VirtuosoWrapper()
print("Getting google categories")

query = """
SELECT 
    ?uri ?name ?full_path
WHERE {
    ?uri a <http://omikron44/ontologies/google_categories>.
    ?uri <http://www.w3.org/2000/01/rdf-schema#label> ?name.
    ?uri <http://omikron44/ontologies/google_categories#full_path> ?full_path.
}
"""

response = virtuoso.get(query=query)
google_categories = {}
for google_category in response["results"]["bindings"]:
    google_categories[google_category["uri"]["value"]] = {
        "term": google_category["name"]["value"],
        "full_path": google_category["full_path"]["value"],
    }

print("Getting merchant categories")
query = """
    SELECT DISTINCT ?product_type
        WHERE {
        ?p a <http://omikron44/ontologies/products>.
        ?p <http://omikron44/ontologies/products#brand> ?brand .
        ?brand a <http://omikron44/ontologies/brands>.
        ?brand <http://omikron44/ontologies/tags#hasTag> "valid".
        ?p <http://omikron44/ontologies/products#product_type> ?product_type .
        } 
    """

# We will use only categories from products that are connected to official brands
response = virtuoso.get(query)
merchant_categories = [
    category["product_type"]["value"] for category in response["results"]["bindings"]
]

nlp = spacy.load("en_core_web_lg")

assigned_clusters = {}

print("Assigning categories")

assigned_categories = []
for category in merchant_categories:
    best_match = None
    best_score = 0
    magelon_category = nlp.vocab[category]
    for category_id, google_category in google_categories.items():
        google_category_name = nlp.vocab[google_category["term"]]
        google_category_path = nlp.vocab[google_category["full_path"]]
        term_score = magelon_category.similarity(google_category_name)
        full_path_score = magelon_category.similarity(google_category_path)
        if term_score > best_score or full_path_score > best_score:
            # print(category_id)
            best_match = category_id
            best_score = max(term_score, full_path_score)
    if best_match and best_score > 0.45:
        print(f"Appending category {category}")
        print(f"Appending category {google_categories[best_match]}")
        print(f"Appending category {best_score}")
        assigned_categories.append(
            {
                "Merchant Category": category,
                "Google Category Path": google_categories[best_match],
                "Google Category ID": best_match,
                "Similarity Score": best_score,
            }
        )

# Verify the categories
user_input = input("Verify the assigned_categories categories? (Y/n): ")
if user_input.lower() in ["", "y"]:
    verified_categories = []
    for linked_category in assigned_categories:
        print(linked_category["Merchant Category"])
        print(linked_category["Google Category Path"])
        print(linked_category["Similarity Score"])
        print()
        user_input = input("Keep this object? (Y/n): ")
        # Append or skip based on user's input
        if user_input.lower() in ["", "y"]:
            linked_category["verified"] = 1
            verified_categories.append(linked_category)
            print("Category verified.")
        else:
            linked_category["verified"] = 0
            verified_categories.append(linked_category)
            print("Category unverified.")
        print()
    assigned_categories = verified_categories


output_file = "clusters/assigned_categories.json"
print("Saving categories")
with open(output_file, "w") as file:
    json.dump(assigned_categories, file, indent=4)

print(f"Results saved to {output_file}")