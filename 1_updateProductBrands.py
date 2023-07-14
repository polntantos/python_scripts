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
 (COUNT(?product) AS ?count) (COUNT(?product_all) AS ?count_all)
WHERE {
  ?product a <http://omikron44/ontologies/products>;
           <http://omikron44/ontologies/products#brand> ?brand .
  ?brand a <http://omikron44/ontologies/brands>.
  ?product_all a <http://omikron44/ontologies/products>.
}
"""

virtuoso = VirtuosoWrapper()

while True:
    update_query_response = virtuoso.get(update_query)
    print("update_query_response")
    # print(update_query_response)
    # print(type(update_query_response))
    print(update_query_response[0]['callret-0'])

    count_query_response = virtuoso.get(count_query)
    print("count_query_response currently updated")
    print(count_query_response[0]["count"])
    if int(count_query_response[0]["count"]) >= count_query_response[0]["count_all"]:
        break
