from multiprocessing import Process, Queue
from rdflib import Graph, RDF, RDFS, URIRef, Literal, BNode
from rdflib.namespace import XSD
import pymysql
from classes.RMLmapping import RMLmapping
from classes.VirtuosoWrapper import VirtuosoWrapper

rmlMapping = RMLmapping("mappings/omikron44-ontology-mapping.ttl")
rmlMapping.status.saveStatus()

virtuoso = VirtuosoWrapper()
rowsQueue = Queue()


def getDataFromLogicalTables(mapping, rowsQueue):
    for table in mapping.logicalTables:
        table.construct_table()

        while True:
            data = table.fetch_data()
            if len(data) < 1:
                rowsQueue.put((None, None))
                break
            rowsQueue.put((table.cursor, data))


def convertDBrowsToGraph(mapping, rowsQueue, status, virtuoso):
    while True:
        try:
            cursor, data = rowsQueue.get(timeout=1)
            g = Graph()
            print(f"cursor at {cursor}")
            if data is None and cursor is None:
                print(f"exiting {mapping.name}")
                break

            print(f"Processing Rows")
            for index, row in data.iterrows():
                subjects = []
                for subjectMap in mapping.subjectMap:
                    subjectUri = subjectMap.materialize(row, g)
                    subjects.append(subjectUri)

                for subject in subjects:
                    for objectMap in mapping.mappings:
                        objectMap.materialize(row, subject, g)

            cursorPosition = virtuoso.save(g, cursor)
            print(f"Conversion ended for {cursorPosition}")
            status.saveStatus(mapping.name, cursorPosition)

        except:
            continue  # Exit loop if process 1 has finished


for mapping in rmlMapping.mappings:
    mapping.materialize_triples()

    dbProcess = Process(
        target=getDataFromLogicalTables,
        args=(
            mapping,
            rowsQueue,
        ),
        daemon=True,
    )

    conversionProcess = Process(
        target=convertDBrowsToGraph,
        args=(
            mapping,
            rowsQueue,
            rmlMapping.status,
            virtuoso,
        ),
        daemon=True,
    )

    dbProcess.start()
    print(f"activating dbProcess")
    conversionProcess.start()
    print(f"activating conversion")
    dbProcess.join()
    conversionProcess.join(timeout=20)


# Build a saving status Process with its own queue and redo virtuoso wrapper
