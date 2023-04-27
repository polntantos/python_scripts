import rdflib
import mysql.connector

# Connect to the MySQL database
cnx = mysql.connector.connect(
    user='root', 
    password='password',
    host='192.168.1.2', 
    database='test'
)

# Get the cursor for executing SQL statements
cursor = cnx.cursor()

# Execute a SQL statement to retrieve the data for the Merchant class
query = "SELECT * FROM merchants"
cursor.execute(query)

# Get the fields for the Merchant class
fields = [field[0] for field in cursor.description]

# Create a graph using rdflib
g = rdflib.Graph()

# Bind the namespace for the Merchant class
g.bind("merchant", "http://example.com/ontology/Merchant#")

# Loop through the data for the Merchant class
for merchant_data in cursor:

    # Create a resource for the Merchant class
    merchant = rdflib.URIRef("http://example.com/data/Merchant#" + str(merchant_data[0]))

    # Add triples for each data property of the Merchant class
    for i, field in enumerate(fields):
        if merchant_data[i]:
            g.add((merchant, rdflib.RDFS.label, rdflib.Literal(field)))
            g.add((merchant, rdflib.RDFS.range, rdflib.Literal(merchant_data[i])))

# Serialize the graph in RDF/XML format
rdf_xml = g.serialize(format='xml')
g.serialize(destination="merchant.owl")

# Close the cursor and the connection to the MySQL database
cursor.close()
cnx.close()
