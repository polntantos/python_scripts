# pip install mysql-connector-python

import mysql.connector

cnx = mysql.connector.connect(
    host="172.26.0.2",
    user="root",
    password="password",
    database="test"
)

# Create a cursor object
cursor = cnx.cursor()

# Execute a query
query = "SELECT id,title,merchant_id FROM test.products limit 100;"
cursor.execute(query)


# Fetch the results
results = cursor.fetchall()
print (results)
