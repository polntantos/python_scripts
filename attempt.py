from rdflib import Graph, RDF, RDFS

# Create an RDF graph
g = Graph()

# Load the R2RML mapping into the graph
g.parse("mappings/omikron44-ontology-mapping.ttl", format="turtle")  

# Query for triples with rr:TriplesMap as the type
query = """
PREFIX rr: <http://www.w3.org/ns/r2rml#>
SELECT ?triplesMap
WHERE {
  ?triplesMap a rr:TriplesMap .
}
"""

triples_map_results = g.query(query)

# Loop through the results and extract the predicate-object maps
for result in triples_map_results:
    triples_map = result["triplesMap"]
    # print('triples_map')
    # print(triples_map)

    # Query for the predicate-object maps associated with the triples map
    query = """
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    SELECT ?predicate ?objectMap
    WHERE {
      ?triplesMap rr:predicateObjectMap ?predicateObjectMap .
      ?predicateObjectMap rr:predicate ?predicate .
      ?predicateObjectMap rr:objectMap ?objectMap .
    }
    """

    predicate_object_map_results = g.query(query, initBindings={"triplesMap": triples_map})

    # Loop through the predicate-object map results and extract the column and datatype information
    for result in predicate_object_map_results:
        
        predicate = result["predicate"]
        object_map = result["objectMap"]
        
        # Query for the column and datatype information associated with the object map
        query = """
        PREFIX rr: <http://www.w3.org/ns/r2rml#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?column ?datatype ?termtype
        WHERE {
          ?objectMap rr:column ?column .
          OPTIONAL { ?objectMap rr:datatype ?datatype . }
          OPTIONAL { ?objectMap rr:termType ?termtype . }
        }
        """

        object_map_results = g.query(query, initBindings={"objectMap": object_map})
        # print('object_map_results')
        # print(object_map_results.serialize(format='txt'))
        # exit()
        # Extract the column and datatype information from the object map results
        for result in object_map_results:
            # print(result)
            column = result["column"]
            datatype = result["datatype"]

            print("Predicate:", predicate)
            print("Column:", column)
            print("Datatype:", datatype)
            print("---")
