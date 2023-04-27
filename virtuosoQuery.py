from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST

sparql = SPARQLWrapper("http://192.168.1.5:8890/sparql-auth")
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
queryResults = sparql.query()

results=queryResults._convertJSON()

responseVars=results['head']['vars'] # [ s, p, o ]
len(results['results']['bindings']) #triples
for i in results['results']['bindings']:
    print(i)

for i in results['results']['bindings']:
    print(i['s'],i['p'],i['o'])

def insertGraph():
    sparql_query_template = """
    INSERT IN GRAPH <http://omikron44.com/> {
      <query_string>
    }
    """

    for triple in g.serialize(format="nt").split("\n"):
        sparql_query=sparql_query_template.replace('<query_string>',triple)
        # print(sparql_query)
        sparql.setQuery(sparql_query)
        results = sparql.query()
        # print(results.response.read())