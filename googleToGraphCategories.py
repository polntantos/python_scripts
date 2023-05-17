import rdflib
import re
from classes.VirtuosoWrapper import VirtuosoWrapper

# create RDF graph
# g = rdflib.Graph()

# set namespace
ns = rdflib.Namespace("http://omikron44/ontologies/google_categories/id=")

# dictionary to store parent-child relationships
relationships = {}

# dictionary to store category_name - category_id for later referal
category_dict = {}

categories = open("googleToGraph/categories.txt")

# parse categories and create relationships dictionary
for category in categories:
    parts = category.strip().split("-")
    category_id = parts[0].strip()
    category_struct = parts[1].strip().split(">")
    # category_name = parts[1][len(parent_ids[0]) + 1:]
    category_name = category_struct[len(category_struct) - 1].strip()
    category_name = re.sub("[^a-zA-Z0-9_]+", "_", category_name)
    category_dict[category_name] = category_id

    parent_category_name = category_struct[len(category_struct) - 2].strip()
    parent_category_name = re.sub("[^a-zA-Z0-9_]+", "_", parent_category_name)
    if parent_category_name != category_name:
        relationships[category_id] = {
            "name": category_name,
            "parent": parent_category_name,
        }
    else:
        relationships[category_id] = {"name": category_name}

# print(relationships)
# print(category_dict)

g = rdflib.Graph()
# add triples to graph for each category
for category_id, category_info in relationships.items():
    # create RDF graph
    category = ns[category_id]
    # g.add((category, rdflib.RDF.type, rdflib.OWL.Class))
    g.add((category, rdflib.RDFS.label, rdflib.Literal(category_info["name"])))
    # print(category_info)
    if "parent" in category_info and category_dict[category_info["parent"]] != None:
        parent = category_dict[category_info["parent"]]
        g.add((category, rdflib.RDFS.subClassOf, ns[parent]))

# serialize graph in RDF/XML format .decode("utf-8")
print(g.serialize(format="pretty-xml"))
# g.serialize(destination="categories.ttl") # stores in categories.tll turtle format
# virtuoso = VirtuosoWrapper()

# virtuoso.save(g)
