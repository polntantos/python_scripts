from classes.VirtuosoWrapper import VirtuosoWrapper


update_query = """
DELETE {
  ?product <http://omikron44/ontologies/products#brand> ?oldBrand .
}
INSERT {
  ?product <http://omikron44/ontologies/products#brand> ?brand .
}
WHERE {
  ?product a <http://omikron44/ontologies/products>;
           <http://omikron44/ontologies/products#brand> ?oldBrand .
  ?brand a <http://omikron44/ontologies/brands>;
        <http://omikron44/ontologies/brands#brand> ?oldBrand .
}
"""

count_query = """
SELECT 
 (COUNT(?product) AS ?count)
WHERE {
  ?product a <http://omikron44/ontologies/products>;
           <http://omikron44/ontologies/products#brand> ?brand .
  ?brand a <http://omikron44/ontologies/brands>.
}
"""

virtuoso = VirtuosoWrapper()

while True:
    update_query_response = virtuoso.get(update_query)
    print("update_query_response")
    print(update_query_response["results"]["bindings"][0]["callret-0"]["value"])

    count_query_response = virtuoso.get(count_query)
    print("count_query_response currently updated")
    print(count_query_response["results"]["bindings"][0]["count"]["value"])
    if int(count_query_response["results"]["bindings"][0]["count"]["value"]) > 3150000:
        break
