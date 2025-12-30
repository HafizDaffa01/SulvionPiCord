import sqlite3
import os
from typing import Any, Dict, List, Optional, Tuple, Union

class Database:
    """
    A simple SQLite database wrapper for SPC.
    Handles connections, queries, and common CRUD operations.
    """
    def __init__(self, path: str) -> None:
        """
        Initialize the database connection.
        
        Args:
            path (str): The file path to the SQLite database.
        """
        # Ensure directory exists
        path_abs = os.path.abspath(path)
        dir_name = os.path.dirname(path_abs)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        # Return rows as dicts for easier access
        self.conn.row_factory = sqlite3.Row  # type: ignore
        self.cursor = self.conn.cursor()

    def execute(self, query: str, params: Union[Tuple[Any, ...], List[Any], Dict[str, Any]] = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query.
        
        Args:
            query (str): The SQL query string.
            params: Parameters for the query.
            
        Returns:
            sqlite3.Cursor: The resulting cursor object.
        """
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            # Note: Specific error handling is handled in the bot caller
            raise e

    def get(self, query: str, params: Union[Tuple[Any, ...], List[Any], Dict[str, Any]] = (), one: bool = False) -> Any:
        """
        Retrieve data from the database.
        
        Args:
            query (str): The SELECT query.
            params: Query parameters.
            one (bool): Whether to return only the first result.
            
        Returns:
            Any: A list of results or a single result row.
        """
        try:
            self.cursor.execute(query, params)
            if one:
                return self.cursor.fetchone()
            return self.cursor.fetchall()
        except Exception as e:
            raise e

    def create_table(self, name: str, schema: Union[Dict[str, str], str]) -> None:
        """
        Create a table if it does not exist.
        
        Args:
            name (str): The name of the table.
            schema: A dictionary of {col: type} or a raw SQL schema string.
        """
        if isinstance(schema, dict):
            cols = ", ".join([f"{k} {v}" for k, v in schema.items()])
            q = f"CREATE TABLE IF NOT EXISTS {name} ({cols})"
        else:
            q = f"CREATE TABLE IF NOT EXISTS {name} ({schema})"
        
        self.execute(q)

    def upsert(self, table: str, data: Dict[str, Any], target_col: Optional[str] = None) -> None:
        """
        Insert a row or replace it if it already exists.
        
        Args:
            table (str): The table name.
            data (dict): Dictionary of column-value pairs.
            target_col (str, optional): The target column for upsert logic (not strictly used in simple REPLACE).
        """
        keys = list(data.keys())
        placeholders = ", ".join(["?"] * len(keys))
        columns = ", ".join(keys)
        values = tuple(data.values())

        query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute(query, values)

    def update(self, table: str, where: Dict[str, Any], set_vals: Dict[str, Any]) -> None:
        """
        Update existing rows.
        
        Args:
            table (str): The table name.
            where (dict): Filter conditions {col: val}.
            set_vals (dict): Values to set {col: val}.
        """
        set_clause = ", ".join([f"{k} = ?" for k in set_vals.keys()])
        where_clause = " AND ".join([f"{k} = ?" for k in where.keys()])
        
        values = list(set_vals.values()) + list(where.values())
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        self.execute(query, values)

    def delete(self, table: str, where: Dict[str, Any]) -> None:
        """
        Delete rows matching the conditions.
        
        Args:
            table (str): The table name.
            where (dict): Filter conditions {col: val}.
        """
        where_clause = " AND ".join([f"{k} = ?" for k in where.keys()])
        values = list(where.values())
        
        query = f"DELETE FROM {table} WHERE {where_clause}"
        self.execute(query, values)

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
