from classes.VirtuosoWrapper import VirtuosoWrapper
from rdflib import Graph, URIRef

minmax_query = """
SELECT 
  (MIN(?productCount) AS ?minProductCount) 
  (MAX(?productCount) AS ?maxProductCount) 
  (AVG(?productCount) AS ?avgProductCount)
WHERE
{{
  SELECT (COUNT(?product) AS ?productCount)
  WHERE {
    ?merchant a <http://magelon.com/ontologies/merchants> .
    ?product <http://magelon.com/ontologies/products#merchant_id> ?merchant_id.
    ?merchant <http://magelon.com/ontologies/merchants#id> ?merchant_id.
}GROUP BY ?merchant
}}
"""

merchants_product_count_query = """
SELECT ?merchant (COUNT(?product) AS ?productCount)
WHERE {
  ?merchant a <http://magelon.com/ontologies/merchants> .
  ?product <http://magelon.com/ontologies/products#merchant_id> ?merchant_id.
  ?merchant <http://magelon.com/ontologies/merchants#id> ?merchant_id.
}
GROUP BY ?merchant
ORDER BY ?productCount
"""

virtuoso = VirtuosoWrapper()
response = virtuoso.get(minmax_query)
print(response)

minProductCount = response[0]["minProductCount"]
maxProductCount = response[0]["maxProductCount"]
avgProductCount = response[0]["avgProductCount"]

print(f"min product count {minProductCount}")
print(f"max product count {maxProductCount}")
print(f"avg product count {avgProductCount}")

response = virtuoso.get(merchants_product_count_query)
merchants = []
for merchant_product_count in response:
    merchants.append(
        {
            "merchant": merchant_product_count["merchant"],
            "product_count": merchant_product_count["productCount"],
        }
    )

ranges = [
    "small",
    "small-medium",
    "medium",
    "medium-large",
    "large",
]
product_count_range = int(maxProductCount) - int(minProductCount)
group_size = product_count_range / 5

graph = Graph()

for part, name in enumerate(ranges):
    while True:
        merchant_product_count = merchants.pop(0)

        if int(merchant_product_count["product_count"]) < (group_size * (part + 1)):
            graph.add(
                (
                    URIRef(merchant_product_count["merchant"]),
                    URIRef("http://magelon.com/ontologies/merchants#merchant-size"),
                    URIRef(f"http://magelon.com/ontologies/magelon-merchant-size/{name}"),
                )
            )
        else:
            merchants.insert(0, merchant_product_count)
            break
if len(merchants) > 0:
    for merchant_product_count in merchants:
        graph.add(
            (
                URIRef(merchant_product_count["merchant"]),
                URIRef("http://magelon.com/ontologies/merchants#merchant-size"),
                URIRef(f"http://magelon.com/ontologies/magelon-merchant-size/large"),
            )
        )
graph.serialize(destination="merchant-tags.ttl", format="turtle")
virtuoso.save(graph)

delete_merchants_query = """
DELETE
WHERE {
  ?merchant a <http://magelon.com/ontologies/merchants> .
  ?merchant <http://magelon.com/ontologies/merchants#id> ?merchant_id.

  FILTER NOT EXISTS {
    ?product <http://magelon.com/ontologies/products#merchant_id> ?merchant_id.
  }
}
"""
virtuoso.get(delete_merchants_query)