from classes.VirtuosoWrapper import VirtuosoWrapper

# object_type ="<http://omikron44/ontologies/magelon-products>"
object_type = "<http://omikron44/ontologies/magelon-product-families>"
# PREFIX ns: <http://omikron44/ontologies/magelon-products>
delete_query = f"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ns: {object_type}

DELETE WHERE {{
  ?s rdf:type ns: .
  ?s ?p ?o .
}} Limit 5000
"""

count_query = f"""
SELECT 
 (COUNT(?object) AS ?count)
WHERE {{
  ?object a {object_type}.
}}
"""

virtuoso = VirtuosoWrapper()

while True:
    update_query_response = virtuoso.get(delete_query)
    print("update_query_response")
    print(update_query_response["results"]["bindings"][0]["callret-0"]["value"])

    count_query_response = virtuoso.get(count_query)
    print("count_query_response currently updated")
    print(count_query_response["results"]["bindings"][0]["count"]["value"])
    if int(count_query_response["results"]["bindings"][0]["count"]["value"]) < 1:
        break
