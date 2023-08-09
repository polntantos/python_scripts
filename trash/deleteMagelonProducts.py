from classes.VirtuosoWrapper import VirtuosoWrapper

# object_type ="<http://omikron44/ontologies/magelon-products>"
# object_type = "<http://omikron44/ontologies/magelon-product-families>"
# PREFIX ns: <http://omikron44/ontologies/magelon-products>
delete_query = f"""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ns: <http://magelon.com/ontologies/>


"""

count_query = f"""
PREFIX ns: "<http://magelon.com/ontologies/>"

SELECT 
 (COUNT(?object) AS ?count)
WHERE {{
  ?object a ns:attributes.
}}
"""

virtuoso = VirtuosoWrapper()

while True:
    update_query_response = virtuoso.get(delete_query)
    print("update_query_response")
    print(update_query_response)
