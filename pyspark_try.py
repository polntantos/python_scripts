import pyspark
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("myRdfSpark.com")
    .config(
        "spark.driver.extraClassPath",
        "jars/mysql-connector-j-8.0.33/mysql-connector-j-8.0.33.jar",
    )
    .config("spark.executor.memory", "4g")
    .config("spark.driver.memory", "4g")
    .master("local")
    .getOrCreate()
)

properties = {
    "driver": "com.mysql.cj.jdbc.Driver",
    "user": "root",
    "password": "password",
    # "database":"homestead",
}

df = spark.read.jdbc(
    url="jdbc:mysql://192.168.10.30:3306/test",
    table="feeds",
    properties=properties,
)

# print(df.collect())
print(df.show())


# .option("dbtable","products") \
# .option("url", "jdbc:mariadb://192.168.10.30:3306/homestead") \
# print(type(df))
# df.show()
