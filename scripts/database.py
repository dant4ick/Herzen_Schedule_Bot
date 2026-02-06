import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.create_table()

    def create_table(self):
        with self.connection:
            self.connection.execute("""CREATE TABLE IF NOT EXISTS users 
                                       (user_id    BIGINT  UNIQUE NOT NULL PRIMARY KEY, 
                                        group_id   INTEGER NOT NULL, 
                                        sub_group  INTEGER NOT NULL DEFAULT (0), 
                                        mailing    STRING  DEFAULT NULL);""")

    def add_user(self, user_id, group_id, sub_group):
        with self.connection:
            self.connection.execute(
                "INSERT INTO users (user_id, group_id, sub_group) VALUES (?, ?, ?) "
                "ON CONFLICT (user_id) DO UPDATE SET group_id = ?, sub_group = ?",
                (user_id, group_id, sub_group, group_id, sub_group)
            )

    def get_user(self, user_id):
        with self.connection:
            user_data = self.connection.execute(
                "SELECT group_id, sub_group FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
        return user_data

    def set_mailing_time(self, user_id: int, mailing_time: str):
        with self.connection:
            self.connection.execute(
                "UPDATE users SET mailing = ? WHERE user_id = ?",
                (mailing_time, user_id)
            )

    def del_mailing_time(self, user_id: int):
        with self.connection:
            self.connection.execute(
                "UPDATE users SET mailing = NULL WHERE user_id = ?",
                (user_id,)
            )

    def get_mailing_time(self, user_id: int):
        with self.connection:
            mailing_time = self.connection.execute(
                "SELECT mailing FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
        return mailing_time[0] if mailing_time else None

    def get_mailing_list(self):
        with self.connection:
            mailing_list = self.connection.execute(
                "SELECT user_id, mailing FROM users WHERE mailing IS NOT NULL"
            ).fetchall()
        return mailing_list

    def del_user(self, user_id):
        with self.connection:
            self.connection.execute(
                "DELETE FROM users WHERE user_id = ?",
                (user_id,)
            )

    def get_all_id(self):
        with self.connection:
            all_user_ids = self.connection.execute(
                "SELECT user_id FROM users"
            ).fetchall()
        return all_user_ids
