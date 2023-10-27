import os
import sqlite3


class UserDB:
    """Context Manager class for the SQLite DataBase"""
    basedir = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, db_filename: str=None, path: str=None) -> None:
        self.db_filename = db_filename if db_filename else ":memory:"
        self.path = path if path else self.basedir

    def __enter__(self):
        os.chdir(self.path)
        self.conn = sqlite3.connect(self.db_filename)
        self.c = self.conn.cursor()
        self.load_db()
        return self
    
    def __exit__(self, exc_type, exc_val, traceback):
        self.conn.close()


    def create_db_table(self):
        self.c.execute("""CREATE TABLE users (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                USERNAME          TEXT    NOT NULL,
                EMAIL             TEXT    NOT NULL,
                PASSWORD          TEXT    NOT NULL,
                JOINED            TEXT    NOT NULL
        )""")


    def load_db(self):
        try:
            self.c.execute("SELECT * from users")
        except:
            self.create_db_table()
            print('Created new Table in database')
        else:
            print('DataBase Exists')

    def add_user(self, user: dict):
        with self.conn:
            self.c.execute("INSERT INTO users(username, email, password, joined) VALUES \
                    (:username, :email, :password, :joined)", user)
            
    def get_users(self):
        self.c.execute("SELECT * from users")
        return self.c.fetchall()

    def get_user_by_id(self, id: int):
        self.c.execute("SELECT * FROM users WHERE id=:id", {"id": id})
        return self.c.fetchone()
    
    def get_user_by_email(self, email: str):
        self.c.execute("SELECT * FROM users WHERE email=:email", {"email": email})
        return self.c.fetchone()

    def update_username(self, id: int, username: str):
        with self.conn:
            self.c.execute("""UPDATE users SET username=:username
                    WHERE id=:id""", {"username": username, "id": id})
            
    def delete_user(self, id: int):
        with self.conn:
            self.c.execute("DELETE from users WHERE id=:id", {'id': id})