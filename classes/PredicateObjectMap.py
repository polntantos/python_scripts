from rdflib import Graph, URIRef, RDF, Literal


class PredicateObjectMap:
    def __init__(self, name, termType, column, datatype, predicate) -> None:
        self.name = name
        self.termType = termType
        self.column = column
        self.datatype = datatype
        self.predicate = predicate

    def materialize(self, row, subject, graph: Graph):
        predicate = URIRef(self.predicate.toPython())

        columnName = self.column.toPython()
        if row[columnName] != None and row[columnName] != "" and row[columnName] != "NaN" and row[columnName] != "NaT" and row[columnName] != "NULL":
            objectValue = Literal(row[columnName])
            graph.add((subject, predicate, objectValue))
            # print(objectValue)
            # print(type(objectValue))
            # exit()
