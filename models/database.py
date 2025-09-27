import sqlite3

class Database(object):
    def __init__(self, path):
        self.path = path

    def connect_db(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        return cursor, con
