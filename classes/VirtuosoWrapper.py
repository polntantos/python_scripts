from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST
import re
import time


class VirtuosoWrapper:
    def __init__(self) -> None:
        self.connect()

    def connect(self) -> None:
        self.sparql = SPARQLWrapper("http://localhost:8890/sparql-auth")
        self.sparql.addDefaultGraph("http://omikron44.com/")
        self.sparql.setHTTPAuth(DIGEST)
        self.sparql.setCredentials("dba", "mydbapassword")
        self.sparql.setMethod(POST)
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(40000)

    def save(self, triplesGraph):
        triplesString = triplesGraph.serialize(format="nt")
        chunks = triplesString.split("\n")

        chunk_size = 200
        print(f"converting triples")
        for i in range(0, len(chunks), chunk_size):
            result = self.insertChunk(chunks[i : i + chunk_size])
            # print(f"triples pushed in virtuoso")
            if result is not True:
                return False

        return True

    def insertChunk(self, triples):
        sparql_query_template = """INSERT DATA {
                    <query_string>
                }"""

        triples = [
            triple for triple in triples if not re.search(r"(?i)(NaN|NaT)", triple)
        ]  # filter nan and nat values
        triplesString = " ".join(triples)
        sparql_query = sparql_query_template.replace("<query_string>", triplesString)
        self.sparql.setQuery(sparql_query)
        attempts = 0
        while attempts < 3:
            try:
                results = self.sparql.query()
                break
            except Exception as e:
                print("An error occurred:", e)

            attempts += 1
            time.sleep(10)

        if attempts == 3:
            print("Maximum attempts reached. Exiting script.")
            return False
        else:
            return True

    def get(self, query):
        self.sparql.setQuery(query)
        results = self.sparql.query()._convertJSON()
        answer = []

        for row in results["results"]["bindings"]:
            row_object = {}
            for field in results["head"]["vars"]:
                if field in row:
                    row_object[field] = row[field]["value"]
            answer.append(row_object)

        return answer

    def getGraph(self, query):
        self.sparql.setQuery(query)
        results = self.sparql.query()._convertJSONLD()

        return results

    def getAll(self, query):
        results = []
        offset = 0
        while True:
            formated_query = f"""
            {query}
            OFFSET {offset}
            LIMIT 10000
            """
            query_results = self.get(formated_query)
            results.extend(query_results)
            if len(query_results) < 10000:
                break

            offset += len(results)
        return results
