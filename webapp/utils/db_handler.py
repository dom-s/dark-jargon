import sqlite3
from datetime import datetime
from typing import Union


class DB:
    def __init__(self, db_path: str):
        try:
            self.conn = sqlite3.connect(db_path)
        except:
            self.conn = None

    def _get_timestamp(self):
        return int(datetime.now().timestamp())


class DarkTermDB(DB):

    def __init__(self, db_path):
        super().__init__(db_path)

    def fetch_verified(self):
        content = self.conn.cursor().execute(
            'SELECT dark_term, definition, definition_source FROM verified').fetchall()
        return content

    def insert_verified(self, dark_term: str, source: Union[str, None], definition: str, definition_source):
        source = '' if not source else source
        t = (dark_term, source, definition, definition_source)
        self.conn.cursor().execute(
            'INSERT INTO verified (dark_term, source, definition, definition_source) VALUES (?, ?, ?, ?)', t)
        self.conn.commit()

    def fetch_collab(self):
        content = self.conn.cursor().execute(
            '''SELECT dark_term_id, dark_term, definition, definition_source, user_name, thumbs_up, thumbs_down
                FROM collab WHERE is_deleted = 0''').fetchall()
        return content

    def fetch_collab_for_file_dump(self):
        content = self.conn.cursor().execute(
            '''SELECT dark_term, definition, definition_source, user_name, thumbs_up, thumbs_down
                FROM collab WHERE is_deleted = 0''').fetchall()
        return content

    def insert_collab(self, dark_term: str, definition: str, definition_source: str, user_name: Union[str, None]):
        timestamp = int(datetime.now().timestamp())
        user_name = 'N/A' if not user_name else user_name
        t = (dark_term, definition, definition_source, timestamp, user_name)
        self.conn.cursor().execute(
            '''INSERT INTO collab (dark_term, definition, definition_source, timestamp, user_name)
                VALUES (?, ?, ?, ?, ?)''', t)
        self.conn.commit()

    def thumbs_up(self, dark_term_id: int):
        t = (dark_term_id, )
        self.conn.cursor().execute(
            'UPDATE collab SET thumbs_up = thumbs_up+1 WHERE dark_term_id = ?', t)
        self.conn.commit()

    def thumbs_down(self, dark_term_id: int):
        t = (dark_term_id,)
        self.conn.cursor().execute(
            'UPDATE collab SET thumbs_down = thumbs_down+1 WHERE dark_term_id = ?', t)
        self.conn.commit()


class LogDB(DB):

    def __init__(self, db_path):
        super().__init__(db_path)

    def log_verified(self, ip_addr):
        ts = self._get_timestamp()
        t = (ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO verified (timestamp, ip_addr) VALUES (?, ?)', t)
        self.conn.commit()

    def log_dark_term_verified_click(self, dark_term, ip_addr):
        ts = self._get_timestamp()
        t = (dark_term, ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO dark_term_verified (dark_term, timestamp, ip_addr) VALUES (?, ?, ?)', t)
        self.conn.commit()

    def log_collab_get(self, ip_addr):
        ts = self._get_timestamp()
        t = (ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO dark_term_collab_get (timestamp, ip_addr) VALUES (?, ?)', t)
        self.conn.commit()

    def log_dark_term_collab_click(self, dark_term, ip_addr):
        ts = self._get_timestamp()
        t = (dark_term, ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO dark_term_collab_post (dark_term, timestamp, ip_addr) VALUES (?, ?, ?)', t)
        self.conn.commit()

    def log_thumbs_up(self, dark_term_id, ip_addr):
        ts = self._get_timestamp()
        t = (dark_term_id, ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO thumbs_up (dark_term_id, timestamp, ip_addr) VALUES (?, ?, ?)', t)
        self.conn.commit()

    def log_thumbs_down(self, dark_term_id, ip_addr):
        ts = self._get_timestamp()
        t = (dark_term_id, ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO thumbs_down (dark_term_id, timestamp, ip_addr) VALUES (?, ?, ?)', t)
        self.conn.commit()

    def log_download(self, ip_addr):
        ts = self._get_timestamp()
        t = (ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO download (timestamp, ip_addr) VALUES (?, ?)', t)
        self.conn.commit()

    def log_download_file(self, dataset, ip_addr):
        ts = self._get_timestamp()
        t = (dataset, ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO download_file (dataset, timestamp, ip_addr) VALUES (?, ?, ?)', t)
        self.conn.commit()

    def log_about(self, ip_addr):
        ts = self._get_timestamp()
        t = (ts, ip_addr)
        self.conn.cursor().execute(
            'INSERT INTO about (timestamp, ip_addr) VALUES (?, ?)', t)
        self.conn.commit()
