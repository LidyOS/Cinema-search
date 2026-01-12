import os
import sqlite3
from typing import Any


class MovieData:
    def __init__(self) -> None:
        # self.db_name = 'MovieData'
        self.db_path = '/app/data/MovieData.db'
        self.stats_table = 'stats'
        self.init_stats_table()

    def get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def table_exists(self, table_name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            return cursor.fetchone()[0] > 0


    def create_table(self, table_name: str, columns: list[str]) -> None:
        with self.get_connection() as conn:
            conn.execute(f"CREATE TABLE  IF NOT EXISTS {table_name} ({', '.join(columns)})")
            conn.commit()


    def insert(self, table_name: str, headers: list[str], values: list[list[Any]]) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({
                    ', '.join(['?' for _ in values])
                    })', values)
            conn.commit()


    def init_stats_table(self) -> None:
        self.create_table(self.stats_table, ['id INTEGER PRIMARY KEY AUTOINCREMENT', 'user_name TEXT'
                                             , 'query TEXT', 'original_title TEXT'])


    def select_queries_by_user(self, user_name: str) -> list[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT query, original_title FROM {self.stats_table}\
                            WHERE user_name = ? ORDER BY id DESC LIMIT 30', (user_name, ))
            return cursor.fetchall()


    def select_stats_by_user(self, user_name: str) -> list[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT original_title, count(*) FROM {self.stats_table}\
                            WHERE user_name = ? group by original_title\
                            ORDER BY count(*) DESC LIMIT 30', (user_name, ))
            return cursor.fetchall()


    def add_user_query(self, query: str, user_name: str, original_title: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'INSERT INTO {self.stats_table} \
                           (user_name, query, original_title) VALUES (?, ?, ?)', (user_name, query, original_title))
            conn.commit()
