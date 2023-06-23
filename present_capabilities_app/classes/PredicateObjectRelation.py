from rdflib import Graph, URIRef, RDF, Literal
import re


class PredicateObjectRelation:
    def __init__(self, name, termType, template) -> None:
        self.name = name
        self.termType = termType
        self.template = template

    def materialize(self, row, subject, graph: Graph):
        objectTemplate = self.template
        keys = re.findall(r"{(\w+)}", objectTemplate)
        for key in keys:
            objectTemplate = objectTemplate.replace(f"{{{key}}}", f"{row[key]}")

        objectUri = URIRef(objectTemplate)
        graph.add((subject, self.termType, objectUri))
