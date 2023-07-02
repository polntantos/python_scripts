from classes.VirtuosoWrapper import VirtuosoWrapper
import re
import click
import json

virtuoso = VirtuosoWrapper()

brands_query = """
    SELECT ?brand_uri ?name
    WHERE {
        ?brand_uri a <http://omikron44/ontologies/brands> .
        ?brand_uri <http://omikron44/ontologies/brands#brand> ?name .
    }"""

brands = virtuoso.getAll(brands_query)

transformed_array = [
    re.sub(r"[^a-z0-9]+", "", brand["name"].lower())
    for brand in brands
    if not re.search(r"[>/#?$%^&*()]+", brand["name"])
]

duplicates = {}
for value in brands:
    term = re.sub(r"[^a-zA-Z]+", "", value["name"].lower())
    if transformed_array.count(term) > 1:
        if term not in duplicates:
            duplicates[term] = []
        duplicates[term].append(value)

duplicate_remains = []

for dupli_name, duplicate_array in duplicates.items():
    for index, duplicate_brand in enumerate(duplicate_array):
        print(f"{index} : {duplicate_brand['name']}")
        # print(type(duplicate_brand))
    userInput = input(f"Select a brand to validate 0-{len(duplicate_array)-1}:")
    duplicate_remains.append(duplicate_array[int(userInput)])

print(duplicate_remains)
with open("duplicate_remains.json", "w") as dr:
    json.dump(duplicate_remains, dr)

with open("duplicate_remains.json", "r") as dr:
    duplicate_remains = json.load(dr)

duplicate_invalidates = []
for dupli_name, duplicate_array in duplicates.items():
    for index, duplicate_brand in enumerate(duplicate_array):
        if duplicate_brand not in duplicate_remains:
            print(duplicate_brand)
            duplicate_invalidates.append(duplicate_brand)

print(duplicate_invalidates)
with open("duplicate_invalidates.json", "w") as dr:
    json.dump(duplicate_invalidates, dr)

with open("duplicate_invalidates.json", "r") as dr:
    duplicate_invalidates = json.load(dr)

for duplicate_invalidate in duplicate_invalidates:
    if duplicate_invalidate in brands:
        brands.remove(duplicate_invalidate)

brands = [brand for brand in brands if not re.search(r"[>/#?$%^&*()]+", brand["name"])]

result_dict = {}

# check if valid brands are contained in other brands
for i, value in enumerate(transformed_array):
    contained_values = []
    for j, other_value in enumerate(transformed_array):
        if i != j and value in other_value and value != "":
            contained_values.append(other_value)
    if contained_values:
        result_dict[value] = contained_values

len(result_dict.values())
for result_key, result_list in result_dict.items():
    print(result_key)
    print(result_list)

flattened_list = set([item for sublist in result_dict.values() for item in sublist])
print(duplicates)
