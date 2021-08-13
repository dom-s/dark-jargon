import ast
import datetime
import os
import re
import sqlite3
from datetime import datetime


class DBHandler:
    def __init__(self, db_dir: str, db_name: str, limit=10000):
        self.cursor = sqlite3.connect(os.path.join(db_dir, db_name)).cursor()
        self.is_darkode = 'darkode' in db_name
        self.table_name = re.sub(r'_.+$', '', db_name)
        self.limit = limit

    def _fetch_comments_other(self, term: str):
        query = f"SELECT title, body FROM posts WHERE posts MATCH '\"{term}\"'"
        if self.limit:
            query += f" LIMIT {self.limit}"
        result = self.cursor.execute(query).fetchall()

        if len(result) > 0:
            _, comments = zip(*result)
            return [ast.literal_eval(comment) for comment in comments], []
        else:
            return [], []

    def _fetch_comments_darkode(self, term: str):
        query = f"SELECT body, timestamp FROM posts WHERE posts MATCH '\"{term}\"'"
        if self.limit:
            query += f" LIMIT {self.limit}"
        result = self.cursor.execute(query).fetchall()
        if len(result) > 0:
            comments, timestamps = zip(*result)
            timestamps = [datetime.fromtimestamp(float(timestamp)) for timestamp in timestamps]
            return comments, timestamps
        else:
            return [], []

    def fetch_comments(self, term: str):
        if self.is_darkode:
            return self._fetch_comments_darkode(term)
        else:
            return self._fetch_comments_other(term)
