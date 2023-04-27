from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST
import re


class VirtuosoWrapper:
    def __init__(self) -> None:
        self.connect()

    def connect(self) -> None:
        self.sparql = SPARQLWrapper("http://localhost:8890/sparql-auth")
        self.sparql.setHTTPAuth(DIGEST)
        self.sparql.setCredentials("dba", "mydbapassword")
        self.sparql.setMethod(POST)
        self.sparql.setReturnFormat(JSON)

    def insert(self, triples):
        sparql_query_template = """INSERT IN GRAPH <http://omikron44.com/> {
            <query_string>
        }"""
        triplesString = triples.serialize(format="nt")
        sparql_query = sparql_query_template.replace("<query_string>", triplesString)
        sparql_query = sparql_query.replace("\n", "")
        # print(sparql_query)

        self.sparql.setQuery(sparql_query)
        results = self.sparql.query()
        # print(results.response.read())
