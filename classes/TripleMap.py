from rdflib import Graph
from classes.VirtuosoWrapper import VirtuosoWrapper
from classes.LogicalTable import LogicalTable
from classes.PredicateObjectMap import PredicateObjectMap
from classes.PredicateObjectRelation import PredicateObjectRelation
from classes.SubjectMap import SubjectMap


class TripleMap:
    def __init__(self, name, triplesMapGraph: Graph) -> None:
        self.name = name
        self.triplesMapGraph = triplesMapGraph
        self.logicalTables = []
        self.mappings = []
        self.subjectMap = []
        self.digest_triples_map()

    def digest_triples_map(self) -> None:
        self.set_logical_tables()
        self.set_subject_mappings()
        self.set_predicate_object_mappings()

    def set_logical_tables(self) -> None:
        logical_table_query = f"""
        PREFIX rr: <http://www.w3.org/ns/r2rml#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?triplesMap ?query ?type
        WHERE {{
            <{self.name}> rr:logicalTable ?logicalTable .
            OPTIONAL{{
                ?logicalTable rr:sqlQuery ?query.
                BIND("sqlQuery" AS ?type)
            }}
            OPTIONAL{{
                ?logicalTable rr:table ?query.
                BIND("table" AS ?type)
            }}
        }}
        """

        results = self.triplesMapGraph.query(logical_table_query)
        for result in results:
            logicalTable = LogicalTable(self.name, result["type"], result["query"])
            self.logicalTables.append(logicalTable)
            # if it has query or it has table act accordingly

    def set_predicate_object_mappings(self) -> None:
        predicate_object_query = f"""
        PREFIX rr: <http://www.w3.org/ns/r2rml#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?objectMap ?column ?datatype ?termType ?predicate ?template
        WHERE {{
            <{self.name}> rr:predicateObjectMap ?predicateObjectMap.
            ?predicateObjectMap rr:objectMap ?objectMap.
            ?objectMap rdf:type rr:ObjectMap;
                    rr:termType ?termType.
            OPTIONAL{{?objectMap rr:template ?template.}}
            OPTIONAL{{?objectMap rr:datatype ?datatype.}}
            OPTIONAL{{?objectMap rr:column ?column.}}
            ?predicateObjectMap rr:predicate ?predicate.
        }}
        """

        results = self.triplesMapGraph.query(predicate_object_query)

        for result in results:
            if result["termType"].toPython() == "http://www.w3.org/ns/r2rml#IRI":
                # print(result['termType'])
                predicateObjectMap = PredicateObjectRelation(
                    self.name, result["termType"], result["template"]
                )
            else:
                predicateObjectMap = PredicateObjectMap(
                    self.name,
                    result["termType"],
                    result["column"],
                    result["datatype"],
                    result["predicate"],
                )
            self.mappings.append(predicateObjectMap)

    def set_subject_mappings(self):
        subject_query = f"""
        PREFIX rr: <http://www.w3.org/ns/r2rml#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?class ?termType ?template
        WHERE {{
            <{self.name}> rr:subjectMap ?subjectMap.
            ?subjectMap rr:template ?template;
                        rr:termType ?termType.
            OPTIONAL{{?subjectMap rr:class ?class.}}
        }}
        """

        results = self.triplesMapGraph.query(subject_query)

        for result in results:
            # print(result)
            self.subjectMap.append(
                SubjectMap(result["template"], result["termType"], result["class"])
            )

    def materialize_triples(self):
        virtuoso = VirtuosoWrapper()
        for table in self.logicalTables:
            counter = 0
            table.construct_table()

            while True:
                counter += 1
                data = table.fetch_data()
                if len(data) < 1:
                    break

                g = Graph()

                for index, row in data.iterrows():
                    subjects = []
                    for subjectMap in self.subjectMap:
                        subjectUri = subjectMap.materialize(row, g)
                        subjects.append(subjectUri)

                    for subject in subjects:
                        for objectMap in self.mappings:
                            objectMap.materialize(row, subject, g)

                g.serialize(
                    destination=f"{table.name}-{counter}-test.ttl", format="turtle"
                )
                virtuoso.insert(g)
