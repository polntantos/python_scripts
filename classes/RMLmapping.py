#This class represents the mapping and its logic
from rdflib import Graph, RDF, RDFS, URIRef, Literal, BNode

from classes.TripleMap import TripleMap

class RMLmapping:

    def __init__(self, mapping) -> None:
        self.mapping = mapping
        self.mappings = []
        self.digest_mapping()

    def digest_mapping(self) -> None:
        # Create an RDF graph
        g = Graph()

        # Load the R2RML mapping into the graph
        g.parse(self.mapping, format="turtle")
        # g.serialize(format="pretty-xml",destination="mapping.xml")
        self.graph=g
        self.get_triple_maps()

    def get_triple_maps(self) -> None:
        query = """
            PREFIX rr: <http://www.w3.org/ns/r2rml#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?triplesMapName ?triplesMap
            WHERE {
                ?triplesMapName a rr:TriplesMap.
            }
            """
        
        results = self.graph.query(query)

        for result in results:
            print(result["triplesMapName"])
            triplemap = TripleMap(result["triplesMapName"],self.graph)
            self.mappings.append(triplemap)

    def perform_conversion(self):
        for mapping in self.mappings:
            mapping.materialize_triples()
