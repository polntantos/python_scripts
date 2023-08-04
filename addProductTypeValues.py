import json

from classes.VirtuosoWrapper import VirtuosoWrapper

virtuoso = VirtuosoWrapper()

with open("clusters/assigned_categories.json") as f:
    data = json.load(f)

    for category_link in data:
        if category_link["verified"] == 1:
            print(category_link)

            google_category_id = category_link["Google Category ID"]
            merchant_category = category_link["Merchant Category"]
            query = f"""
                INSERT {{
                ?product <http://omikron44/ontologies/products#google_product_type> <{google_category_id}> .
                }}
                WHERE {{
                ?product a <http://omikron44/ontologies/products> ;
                        <http://omikron44/ontologies/products#product_type> '{merchant_category}' .
                }}
            """

            result = virtuoso.get(query)
            print(result["results"]["bindings"])
