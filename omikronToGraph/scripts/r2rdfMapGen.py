import pymysql

# Define the connection details for the MySQL database
conn = pymysql.connect(host='192.168.1.2', user='root', password='password', database='test')

def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


# Define the SQL query to retrieve the schema information
sql_query = """
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'test'
"""

# Execute the SQL query
cursor = conn.cursor()
cursor.execute(sql_query)

# Create a dictionary to store the table information
tables = {}

# Iterate over the rows returned by the query
for row in cursor:
    # print(row) # you can uncomment this line to see how every row is formed
    table_name = row[0]
    column_name = row[1]
    data_type = row[2]

    # If this is the first time we've seen this table, add it to the dictionary
    if table_name not in tables:
        tables[table_name] = {'columns': [], 'pk': []}

    # Add the column to the table's list of columns
    tables[table_name]['columns'].append(column_name)

    # If this column is part of the primary key, add it to the table's list of primary key columns
    if column_name == 'id':
        tables[table_name]['pk'].append(column_name)

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
    mapping += f'<#Table_{table_name}>\n'
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
    for column_name in table_info['columns']:
        mapping += f'\trr:predicateObjectMap[ \n'
        mapping += f'\t\trr:predicate ex:{to_camel_case(column_name)}; \n'
        mapping += f'\t\trr:objectMap [rr:column "{column_name}"]; \n'
        mapping += f'\t]; \n\n'

    mapping += f'.\n\n'

cursor.close()
conn.close()
# Print the mapping file
print(mapping)

# Open a file for writing
with open("r2rml_mapping.ttl", "w") as f:
    # Write the R2RML mapping to the file
    f.write(mapping)

