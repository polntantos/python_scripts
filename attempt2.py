from rdflib import Graph, RDF, RDFS, URIRef, Literal, BNode
from rdflib.namespace import XSD
import pymysql
from classes.RMLmapping import RMLmapping

rmlMapping = RMLmapping("mappings/omikron44-ontology-mapping.ttl")
rmlMapping.perform_conversion()
