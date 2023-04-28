import pymysql
import pandas as pd
from rdflib import Graph, URIRef, RDF
import re


class LogicalTable:
    def __init__(self, name, type, construct=None, cursor=0) -> None:
        self.name = name
        self.type = type
        self.construct = f"{construct} LIMIT 10"
        self.cursor = cursor
        print(cursor)
        exit()

    def construct_table(self):
        if self.type.toPython() == "sqlQuery":
            # sql query and return pointer
            conn = pymysql.connect(
                host="localhost", user="root", password="password", database="test"
            )
            self.datatable = conn.cursor()
        elif self.type.toPython() == "table":
            print("Reading file :", self.construct)

            self.datatable = self.read_csv_file(self.construct)
        else:
            return None

    def read_csv_file(self, file_path):
        df = pd.read_csv(file_path)
        return df

    def read_database(self, offset=0):
        query = self.construct

        if offset > 0:
            query = f"{query} OFFSET {offset}"

        print("Performing query :", query)
        self.datatable.execute(query)

    def fetch_data(self):
        if self.type.toPython() == "sqlQuery":
            result = self.read_database(self.cursor)
            print("Fetching 10 from start ", self.cursor, " from database.")
            self.cursor += 10
            field_names = [i[0] for i in self.datatable.description]
            # print(type(result))
            # print(result)
            return pd.DataFrame(self.datatable.fetchall(), columns=field_names)

        elif self.type.toPython() == "table":
            start = self.cursor
            self.cursor += 10
            print(f"Fetching {start} to {self.cursor} from database.")
            return self.datatable.iloc[start : self.cursor]
        else:
            return None
