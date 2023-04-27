from rdflib import Graph, URIRef, Namespace
from rdflib.plugins.stores import sparqlstore
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from rdflib.plugins.stores.sparql import SPARQLUpdateStore
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.processor import SPARQLResult
from rdflib.namespace import RDF, RDFS, XSD
from rdflib.plugins.parsers.notation3 import N3Parser
from rdflib.plugins.serializers.turtle import TurtleSerializer
from io import StringIO
import mysql.connector

# Define namespaces
R2RML = Namespace("http://www.w3.org/ns/r2rml#")
RR = Namespace("http://www.w3.org/ns/r2rml#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
EXAMPLE = Namespace("http://example.com/")

# Load R2RML mapping from file
with open("mapping.ttl") as f:
    mapping = f.read()

# Create SPARQLStore backed by a new in-memory graph
graph = Graph()
store = SPARQLStore(graph)
store.open((None, None))

# Load R2RML mapping into the store
update_query = "INSERT DATA { " + mapping + " }"
store.update(update_query)

# Connect to MySQL database
cnx = mysql.connector.connect(user='username', password='password',
                              host='localhost',
                              database='mydatabase')
cursor = cnx.cursor()

# Execute SQL query and fetch results
sql_query = "SELECT * FROM mytable"
cursor.execute(sql_query)
results = cursor.fetchall()

# Map query results to RDF triples
for row in results:
    # Create subject URI
    subject = EXAMPLE["resource/" + str(row[0])]
    
    # Create triples for columns
    for i in range(1, len(row)):
        # Get column name from R2RML mapping
        query = prepareQuery("""
            PREFIX rr: <http://www.w3.org/ns/r2rml#>
            PREFIX ex: <http://example.com/>
            SELECT ?p WHERE {
                <#TriplesMap1> rr:predicateObjectMap [
                    rr:predicate ?p;
                    rr:objectMap [ rr:column "column%d" ]
                ].
            }
        """ % i, initNs={"rr": R2RML, "ex": EXAMPLE})
        results = store.query(query)
        predicate = next(results.bindings)["p"]
        
        # Create object literal
        object = Literal(row[i])
        if type(row[i]) == int:
            object.datatype = XSD.integer
        elif type(row[i]) == float:
            object.datatype = XSD.float
        elif type(row[i]) == bool:
            object.datatype = XSD.boolean
        
        # Add triple to graph
        graph.add((subject, predicate, object))

# Serialize RDF graph to Turtle format and write to file
with open("output.ttl", "wb") as f:
    serializer = TurtleSerializer()
    serializer.serialize(f, graph)
