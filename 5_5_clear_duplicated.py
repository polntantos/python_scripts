from classes.VirtuosoWrapper import VirtuosoWrapper
import json


query = """
PREFIX magelon: <http://magelon.com/ontologies/>

SELECT ?product ?title STRAFTER(str(?predicate), "#") as ?attribute ?value ?label
WHERE {
  # Subquery to find products with duplicate predicates
  {
    SELECT ?product ?predicate (COUNT(?predicate) AS ?count)
    WHERE {
      ?product a magelon:products.
      ?product ?predicate ?value.
      ?value a magelon:attributes.
      FILTER NOT EXISTS{?product <http://magelon.com/ontologies/has_attribute#uknown> ?value}
      FILTER NOT EXISTS{?product <http://magelon.com/ontologies/has_attribute#color> ?value}
    }
    GROUP BY ?product ?predicate
    HAVING (COUNT(?predicate) > 1)
  }

  # Now retrieve the values for each product and predicate
  ?product ?predicate ?value.
  ?value rdfs:label ?label.
  ?product <http://magelon.com/ontologies/products#title> ?title.
}
"""

virtuoso = VirtuosoWrapper()

duplicate_dict={}

results = virtuoso.getAll(query)

for row in results:
  if(row['product'] not in duplicate_dict):
    duplicate_dict[row['product']] = {"title":row["title"],"duplicates":{}}
  if row["attribute"] not in duplicate_dict[row['product']]["duplicates"]:
    duplicate_dict[row['product']]["duplicates"][row["attribute"]]=[]
  duplicate_dict[row['product']]["duplicates"][row["attribute"]].append((row["label"],row["value"]))
  
selections={}
prefered_values = []
print(f"Products with duplicate attributes {len(duplicate_dict.keys())}")
for product_uri,product_info in duplicate_dict.items():
  selections[product_uri]={}
  print(product_info["title"])
  for duplicate_name,duplicates in product_info["duplicates"].items():
    print(f"Select correct value for {duplicate_name}")
    value_dict={}
    default=""
    for i,duplicate in enumerate(duplicates):
      value_dict[str(i)]=duplicate[1]
      if duplicate[1] in prefered_values:
        print(f"{i}:{duplicate[0]} PREFERED")
        default = duplicate[1]
      else:
        print(f"{i}:{duplicate[0]}")
    selection=input("Insert option (empty for default):")
    if(selection in value_dict):
      selections[product_uri][duplicate_name]=value_dict[selection]
      prefered_values.append(value_dict[selection])
    elif selection =="" and default != "":
      selections[product_uri][duplicate_name]=default
    else:
      print("skipped")
    
  #save at every row