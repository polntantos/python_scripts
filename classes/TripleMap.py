from rdflib import Graph
from classes.VirtuosoWrapper import VirtuosoWrapper
from classes.LogicalTable import LogicalTable
from classes.PredicateObjectMap import PredicateObjectMap
from classes.PredicateObjectRelation import PredicateObjectRelation
from classes.SubjectMap import SubjectMap
from multiprocessing import Queue, Process


class TripleMap:
    def __init__(self, name, triplesMapGraph: Graph, status=None) -> None:
        self.name = name
        self.triplesMapGraph = triplesMapGraph
        self.logicalTables = []
        self.mappings = []
        self.subjectMap = []
        self.status = status

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
            triplemapStatus = self.status.status.get(self.name.toPython())
            logicalTable = LogicalTable(
                f"{self.name}-{len(self.logicalTables)}",
                result["type"],
                result["query"],
                triplemapStatus.get(f"{self.name}-{len(self.logicalTables)}"),
            )

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
        self.virtuoso = VirtuosoWrapper()
        rowsQueue = Queue()

        self.dbProcess = Process(
            target=self.getDataFromLogicalTables, args=(rowsQueue,), daemon=True
        )

        self.conversionProcess = Process(
            target=self.convertDBrowsToGraph,
            args=(
                rowsQueue,
                self.status,
            ),
            daemon=True,
        )

        self.dbProcess.start()
        print(f"activating dbProcess")
        self.conversionProcess.start()
        print(f"activating conversion")

        self.dbProcess.join()
        self.conversionProcess.join(timeout=20)

        # g.serialize(
        #     destination=f"/rdf_output/{table.name}-{counter}-test.ttl",
        #     format="turtle",
        # )

    def getDataFromLogicalTables(self, rowsQueue):
        for table in self.logicalTables:
            table.construct_table()

            while True:
                data = table.fetch_data()
                if len(data) < 1:
                    rowsQueue.put((None, None))
                    break
                rowsQueue.put((table.cursor, data))

    def convertDBrowsToGraph(self, rowsQueue, status):
        print(status.status)

        while True:
            try:
                cursor, data = rowsQueue.get(timeout=1)
                g = Graph()
                print(f"cursor at {cursor}")
                if data is None and cursor is None:
                    print(f"exiting {self.name}")
                    break

                print(f"Processing Rows")
                for index, row in data.iterrows():
                    subjects = []
                    for subjectMap in self.subjectMap:
                        subjectUri = subjectMap.materialize(row, g)
                        subjects.append(subjectUri)

                    for subject in subjects:
                        for objectMap in self.mappings:
                            objectMap.materialize(row, subject, g)

                cursorPosition = self.virtuoso.save(g, cursor)
                print(f"Conversion ended for {cursorPosition}")
                status.saveStatus(self.name, cursorPosition)

            except:
                continue  # Exit loop if process 1 has finished
