from rdflib import Graph, URIRef, RDF
import re


class SubjectMap:
    def __init__(self, template, termtype, className=None) -> None:
        self.template = template
        self.termtype = termtype
        self.className = className

    def materialize(self, row, graph: Graph):
        subjectTemplate = self.template

        keys = re.findall(r"{(\w+)}", subjectTemplate)

        for key in keys:
            subjectTemplate = subjectTemplate.replace(f"{{{key}}}", f"{row[key]}")

        subjectUri = URIRef(subjectTemplate)
        if self.className != None:
            graph.add((subjectUri, RDF.type, self.className))

        return subjectUri
