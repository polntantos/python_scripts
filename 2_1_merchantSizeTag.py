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
    ?merchant a <http://omikron44/ontologies/merchants> .
    ?product <http://omikron44/ontologies/products#merchant_id> ?merchant_id.
    ?merchant <http://omikron44/ontologies/merchants#id> ?merchant_id.
}GROUP BY ?merchant
}}
"""

merchants_product_count_query = """
SELECT ?merchant (COUNT(?product) AS ?productCount)
WHERE {
  ?merchant a <http://omikron44/ontologies/merchants> .
  ?product <http://omikron44/ontologies/products#merchant_id> ?merchant_id.
  ?merchant <http://omikron44/ontologies/merchants#id> ?merchant_id.
}
GROUP BY ?merchant
ORDER BY ?productCount
"""

virtuoso = VirtuosoWrapper()
response = virtuoso.get(minmax_query)
bindings = response["results"]["bindings"]

minProductCount = bindings[0]["minProductCount"]["value"]
maxProductCount = bindings[0]["maxProductCount"]["value"]
avgProductCount = bindings[0]["avgProductCount"]["value"]

print(f"min product count {minProductCount}")
print(f"max product count {maxProductCount}")
print(f"avg product count {avgProductCount}")

response = virtuoso.get(merchants_product_count_query)
bindings = response["results"]["bindings"]
merchants = []
for merchant_product_count in bindings:
    merchants.append(
        {
            "merchant": merchant_product_count["merchant"]["value"],
            "product_count": merchant_product_count["productCount"]["value"],
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
                    URIRef("http://omikron44/ontologies/merchants#merchant-size"),
                    URIRef(f"http://omikron44/ontologies/magelon-merchant-size/{name}"),
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
                URIRef("http://omikron44/ontologies/merchants#merchant-size"),
                URIRef(f"http://omikron44/ontologies/magelon-merchant-size/large"),
            )
        )
graph.serialize(destination="merchant-tags.ttl", format="turtle")
virtuoso.save(graph)
