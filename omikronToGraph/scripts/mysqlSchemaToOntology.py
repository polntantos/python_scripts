#pip install pymysql

import pymysql
import rdflib
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import XSD

# Define the connection details for the MySQL database
conn = pymysql.connect(host='192.168.1.2', user='root', password='password', database='test')

def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])

def to_pascal_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component 
    return ''.join(x.title() for x in components)

def plural_to_single(plural_word):
    if plural_word[-3:]=="ses" :
        return plural_word
    else :
        return plural_word.rstrip('s')

sql_query = """
SELECT TABLE_NAME,COLUMN_NAME,IS_NULLABLE,DATA_TYPE,COLUMN_KEY
FROM information_schema.columns
WHERE table_schema = 'test' AND TABLE_NAME in ('products','merchant_feeds','merchants','gos','account_performances','account_reports','account_statuses','clicks')
"""

#Create a dictionary for the column datatype
datatype_mapping = {
    "bigint": XSD.long,
    "double": XSD.double,
    "timestamp": XSD.dateTime,
    "varchar": XSD.string,
    "json": XSD.string,
    "text": XSD.string,
    "longtext": XSD.string,
    "tinyint": XSD.integer,
    "int": XSD.integer,
    "mediumtext": XSD.string,
    "char": XSD.string,
    "date": XSD.date,
    "datetime": XSD.dateTime
}

# Execute the SQL query
cursor = conn.cursor()
cursor.execute(sql_query)

# Create a dictionary to store the table information
tables = {}
table_connections = {}
# Iterate over the rows returned by the query
for row in cursor:
    #print(row)
    table_name = plural_to_single(row[0])
    column_name = row[1]
    is_nullable = row[2]
    data_type = row[3]
    column_key = row[4] # NULL, PRI for Primary or MUL for Foreign key (no relation data)

    # If this is the first time we've seen this table, add it to the dictionary
    if table_name not in tables:
        tables[table_name] = {'columns': {}}
            
    # Create a dictionary to store column data
    column_data = {'nullable':True if is_nullable=='YES' else False,'data_type':data_type}
    
    # If this column is part of the primary key, add it to the table's list of primary key columns
    if column_key == 'PRI':
        column_data['pk']=True
    elif column_key == 'MUL':
        if table_name not in table_connections:
            table_connections[table_name] = {'connections':[]}
        
        table_connections[table_name]['connections'].append(column_name)

    
    # Add the column to the table's list of columns
    tables[table_name]['columns'][column_name]=column_data

# Define namespaces
owl = Namespace("http://www.w3.org/2002/07/owl#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
xsd = Namespace("http://www.w3.org/2001/XMLSchema#")
onto = Namespace("http://www.omikron44.com/ontology/")

# Define a function to create the ontology for a single table
def create_table_ontology(table_dict,table_connections):
    # Define the ontology graph
    g = Graph()
    g.bind('owl', owl)
    g.bind('rdfs', rdfs)
    g.bind('xsd', xsd)
    g.bind('onto', onto)

    # Define the table class
    for table,table_info in table_dict.items():
        # print(table,table_info)
        table_class = onto[to_pascal_case(table)]
        g.add((table_class, RDF.type, owl.Class))
        g.add((table_class, rdfs.label, Literal(to_pascal_case(table))))

        # Define the column properties
        for col_name,col_data in table_info['columns'].items():
            # print(col_name,col_data)
            col_prop = onto[to_pascal_case(col_name)]
            g.add((col_prop, RDF.type, owl.DatatypeProperty))
            g.add((col_prop, rdfs.label, Literal(to_pascal_case(col_name))))
            g.add((col_prop, rdfs.domain, table_class))
            g.add((col_prop, rdfs.range, datatype_mapping[col_data['data_type']]))
    
    for table,connections in table_connections.items():
        print(table,connections['connections'])
        t_subject = onto[to_pascal_case(table)]
        
        for connection in connections['connections']:
            print(connection)
            components = connection.split('_')
            t_object = onto[to_pascal_case('_'.join(components[:-1]))]
            object_property=onto[to_pascal_case('has_'+table)]
            print(t_object+' '+object_property+' '+t_subject)
            g.add((object_property, RDF.type, owl.ObjectProperty))
            g.add((object_property, RDFS.domain, t_object))
            g.add((object_property, RDFS.range, t_subject))
            
            rev_object_property=onto[to_pascal_case('belongs_to_'+'_'.join(components[:-1]))]
            print(t_subject+' '+rev_object_property+' '+t_object)
            g.add((rev_object_property, RDF.type, owl.ObjectProperty))
            g.add((rev_object_property, RDFS.domain, t_subject))
            g.add((rev_object_property, RDFS.range, t_object))
    
    g.serialize(destination='ontology.owl',format='xml')
    #return g.serialize(destination=ontology.owl,format='xml')
    
create_table_ontology(tables,table_connections)


# Create the R2RML mapping file
mapping = '''
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.com/ns#>.

'''

# Iterate over the tables in the dictionary
for table_name, table_info in tables.items():
    # Create the mapping for the table
    mapping += f'<#{to_pascal_case(table_name)}>\n'
    mapping += f'\trr:logicalTable [rr:tableName "{table_name}"];\n'
    #mapping += f'\t #"{table_info}" \n'
    
    # If the table has a primary key, create the mapping for it
    if len(table_info['pk']) > 0:
        mapping += f'\trr:subjectMap [\n'
        mapping += f'\t\trr:template "http://example.com/{table_name}/{{' + '}}{'.join(table_info['pk']) + '}"; \n'
        mapping += f'\t\trr:class ex:{table_name}; \n'
        mapping += f'\t\trr:termType rr:IRI; \n'
        mapping += f'\t];\n\n'
        
    # Create the mapping for each column in the table
    for column_name,column_info in table_info:
        mapping += f'\trr:predicateObjectMap[ \n'
        mapping += f'\t\trr:predicate ex:{to_camel_case(column_name)}; \n'
        mapping += f'\t\trr:objectMap [rr:column "{column_name}"]; \n'
        mapping += f'\t]; \n\n'

    mapping += f'.\n\n'

cursor.close()
# Print the mapping file
print(mapping)

# Open a file for writing
with open("r2rml_mapping.ttl", "w") as f:
    # Write the R2RML mapping to the file
    f.write(mapping)

conn.close()