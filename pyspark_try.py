import pyspark
from pyspark.sql import SparkSession

spark = (
  SparkSession.builder
  .appName('myRdfSpark.com')
  .config("spark.driver.extraClassPath","jars/maria/mariadb-java-client-3.1.4.jar")
  .config("spark.executor.memory", "4g") 
  .config("spark.driver.memory", "4g") 
  .master("local")
  .getOrCreate()
  )

properties={
  "driver":"org.mariadb.jdbc.Driver", 
  "user":"homestead",
  "password":"secret",
  # "database":"homestead",
}

df = spark.read.jdbc(
  url="jdbc:mariadb://192.168.10.30:3306/homestead",
  table="products",
  properties=properties
) 

print(df.collect())
print(df.toLocalIterator())

    
    # .option("dbtable","products") \
    # .option("url", "jdbc:mariadb://192.168.10.30:3306/homestead") \
# print(type(df))
# df.show()