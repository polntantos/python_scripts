from rdflib import Graph, RDF, RDFS, URIRef, Literal, BNode
from rdflib.namespace import XSD
import pymysql
from classes.RMLmapping import RMLmapping


def parse_r2rml_mapping(mapping_file):
    """
    Parse an R2RML mapping file with rdflib, execute the SQL query in the rr:logicalTable,
    and create RDF triples based on the mapping.
    """
    # Create an RDF graph
    g = Graph()

    # Load the R2RML mapping into the graph
    g.parse(mapping_file, format="turtle")

    # Query for triples maps with rr:sqlQuery in the logical table
    query = """
    PREFIX rr: <http://www.w3.org/ns/r2rml#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?triplesMap ?sqlQuery ?column ?datatype ?termType ?objectMap ?predicateObjectMap
    WHERE {
      ?triplesMap a rr:TriplesMap ;
          rr:logicalTable ?logicalTable .
          OPTIONAL{?logicalTable rr:sqlQuery ?sqlQuery } .
      ?predicateObjectMap a rr:PredicateObjectMap;
          rr:objectMap ?objectMap .
              ?objectMap rr:column ?column ;
                         rr:datatype ?datatype ;
                         rr:termType ?termType .

    }
    """
    # What will happen if we spit the queries
    # Try to form a model to wrap the mapping
    # ?predicateObjectMap rr:predicateObjectMap ?predicateObjectMap .
    #   ?predicateObjectMap rr:predicate ?predicate .
    #   ?predicateObjectMap rr:ObjectMap ?objectMap .
    #   ?objectMap rr:column ?column ;
    #              rr:datatype ?datatype ;
    #              rr:termType ?termType .

    results = g.query(query)
    print("results")
    # print(results.serialize(format='json'))
    # Loop through the results and execute the SQL query
    for result in results:
        triples_map = result["triplesMap"]
        print(triples_map)

        sql_query = result["sqlQuery"]
        print(sql_query)

        predicate_object_map = result["predicateObjectMap"]
        print(predicate_object_map)

        object_map = result["objectMap"]
        print(object_map)

        continue
        # column = result["column"]
        # print(column)
        # datatype = result["datatype"]
        # print(datatype)
        # term_type = result["termType"]
        # print(term_type)

        # exit()
        # Execute the SQL query and get the results
        # Here you can replace this step with your own code to execute the SQL query
        # and get the results using a database connector or any other method of your choice
        query_results = execute_sql_query(sql_query)

        # Loop through the query results and create RDF triples based on the mapping
        for query_result in query_results:
            # Create a blank node for the subject
            subject = BNode()

            # Create a URIRef for the predicate
            predicate = URIRef(result["predicate"])

            # Create a Literal for the object with the specified datatype and term type
            if term_type == URIRef("http://www.w3.org/ns/r2rml#Literal"):
                obj = Literal(query_result[column], datatype=datatype)
            else:
                obj = URIRef(query_result[column])

            # Add the triple to the RDF graph
            g.add((subject, predicate, obj))

    return g


def execute_sql_query(sql_query):
    db = connect_to_database()
    cursor = db.cursor()
    # In this example, we return a list of dictionaries as query results
    cursor.execute(sql_query)

    return cursor


# Connect to MySQL database
def connect_to_database():
    return pymysql.connect(
        host="localhost", user="root", password="password", db="test"
    )


# graph=parse_r2rml_mapping("mappings/omikron44-ontology-mapping.ttl")

rmlMapping = RMLmapping("mappings/omikron44-ontology-mapping.ttl")
rmlMapping.perform_conversion()

# graph.serialize(destination='datasets/attempt2.ttl',format='turtle')
