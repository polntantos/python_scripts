from classes.VirtuosoWrapper import VirtuosoWrapper
import re
import json
import nltk
from nltk.corpus import stopwords
import copy

nltk.download("stopwords")


def is_stopword(word):
    stopword_set = set(stopwords.words("english"))  # Get the set of English stopwords
    return word.lower() in stopword_set


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


# Remove first two categories of invalid brands

for duplicate_invalidate in duplicate_invalidates:
    if duplicate_invalidate in brands:
        brands.remove(duplicate_invalidate)

brands = [brand for brand in brands if not re.search(r"[>/#?$%^&*()]+", brand["name"])]

result_dict = {}

# check if valid brands are contained in other brands
for i, value in enumerate(transformed_array):
    contained_values = []
    for j, other_value in enumerate(transformed_array, i):
        if i != j and value in other_value and value != "":
            contained_values.append(other_value)
    if contained_values:
        result_dict[value] = contained_values


# bit_dict = {}

# for i, value in enumerate(brands):
#     if i not in bit_dict:
#         bit_dict[i] = []
#     bit_dict[i].extend(value["name"].lower().split())

# bit_result = {}
# for key, bit in bit_dict.items():
#     print(f"current key {key}")
#     contained_values = []
#     for other_key, other_bit in bit_dict.items():
#         if key != other_key and bit != "":
#             for i in bit:
#                 if i in other_bit:
#                     contained_values.append(brands[other_key]["name"])
#     if contained_values:
#         bit_result[brands[key]["name"]] = contained_values

# with open("bit_result.json", "w") as dr:
#     json.dump(bit_result, dr)

# with open("bit_result.json", "r") as dr:
#     bit_result = json.load(dr)

result_dict = {}
# check if valid brands are contained in other brands
for i, value in enumerate(brands):
    print(f"current key {i}")
    contained_values = []
    for j, other_value in enumerate(brands):
        # print(check_brand)
        if (
            i != j
            and value["name"].lower() in other_value["name"].lower()
            and value["name"] != ""
            and not is_stopword(word)
        ):
            contained_values.append(other_value)
            # if other_value["name"] not in result_dict.keys():
            #     break
    print(contained_values)
    if len(contained_values) > 0:
        result_dict[value["name"]] = contained_values


with open("result_dict2.json", "w") as dr:
    json.dump(result_dict, dr)

with open("result_dict.json", "r") as dr:
    result_dict = json.load(dr)

len(result_dict.values())
for result_key, result_list in result_dict.items():
    print(result_key)
    print(result_list)

flattened_list = set([item for sublist in result_dict.values() for item in sublist])
print(duplicates)
