from classes.VirtuosoWrapper import VirtuosoWrapper


delete_query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ns: <http://omikron44/ontologies/magelon-products>

DELETE WHERE {
  ?s rdf:type ns: .
  ?s ?p ?o .
} Limit 5000
"""

count_query = """
SELECT 
 (COUNT(?product) AS ?count)
WHERE {
  ?product a <http://omikron44/ontologies/magelon-products>.
}
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
