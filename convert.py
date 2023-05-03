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
                rowsQueue.put((None, None, None))
                break
            rowsQueue.put((table.cursor, table.name, data))


def convertDBrowsToGraph(mapping, rowsQueue, status, virtuoso):
    while True:
        try:
            cursor, name, data = rowsQueue.get(timeout=1)
            g = Graph()
            print(f"Cursor at {cursor} for logical table {name}")
            if data is None and name is None and cursor is None:
                print(f"Exiting {name}")
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
            status.saveStatus(name, cursorPosition)

        except:
            continue  # Exit loop if process 1 has finished


for mapping in rmlMapping.mappings:
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
