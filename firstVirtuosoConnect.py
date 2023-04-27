#pip install SPARQLWrapper



from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST

sparql = SPARQLWrapper("http://192.168.1.5:8890/sparql")
sparql.setHTTPAuth(DIGEST)
sparql.setCredentials("dba", "mydbapassword")
sparql.setMethod(POST)
sparql.setReturnFormat(JSON)

sparql_query = """
select * from <http://omikron44.com/> where{
  ?s ?p ?o.
}
"""
sparql.setQuery(sparql_query)

results = sparql.query()
print(results.response.read())

sparql_query_template = """
INSERT IN GRAPH <http://omikron44.com /> {
  <query_string>
}
"""

for triple in g.serialize(format="nt").split("\n"):
    sparql_query = sparql_query_template.replace( '<query_string>', g.serialize(format="nt") )

sparql.setQuery(sparql_query)
results = sparql.query()
print(results.response.read())