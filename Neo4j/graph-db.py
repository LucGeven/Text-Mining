import csv

from neo4j import GraphDatabase
from tqdm import tqdm
import json

class Neo4jConnection:
    def __init__(self, uri, user, password) -> None:
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        self._session = self._driver.session(database='neo4j')

    def query(self, query, db=None):
        assert self._driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self._driver.session(database=db) if db is not None else self._driver.session() 
            response = list(session.run(query))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response

    def add_triple(self, source_entity: str, predicate: str, end_entity: str) -> None:

        query = f"""
        MERGE (n:Entity {{name: '{source_entity}'}})
        MERGE (m:Entity {{name:'{end_entity}'}})
        MERGE (n)-[:{predicate}]->(m)
        """
        self._session.run(query)

    def close(self):
        self._driver.close()

if __name__ == '__main__':
    conn = Neo4jConnection('bolt://localhost:7687', 'neo4j', 'admin')

    with open('found_triples.csv', 'r') as file:
        reader = csv.reader(file)

        for row in tqdm(list(reader)):
            conn.add_triple(row[0], row[1], row[2])
