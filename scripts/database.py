import sqlite3


class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id, group_id, sub_group):
        with self.connection:
            self.cursor.execute("INSERT INTO `users` (user_id, group_id, sub_group) VALUES (?, ?, ?)"
                                "ON CONFLICT (user_id) WHERE user_id = ?"
                                "DO UPDATE SET group_id = ?, sub_group = ?",
                                (user_id, group_id, sub_group, user_id, group_id, sub_group))

    def get_user(self, user_id):
        with self.connection:
            user_data = self.cursor.execute("SELECT group_id, sub_group FROM `users` WHERE user_id = ?",
                                            (user_id,)).fetchone()
        return user_data

    def set_mailing_time(self, user_id: int, mailing_time: str):
        with self.connection:
            self.cursor.execute("UPDATE 'users' SET mailing = ? WHERE user_id = ?", (mailing_time, user_id))

    def del_mailing_time(self, user_id: int):
        with self.connection:
            self.cursor.execute("UPDATE 'users' SET mailing = NULL WHERE user_id = ?", (user_id,))

    def get_mailing_time(self, user_id: int):
        with self.connection:
            mailing_time = self.cursor.execute("SELECT mailing FROM 'users' WHERE user_id = ?", (user_id,)).fetchone()
        return mailing_time[0]

    def get_mailing_list(self):
        with self.connection:
            self.cursor.execute("SELECT user_id, mailing FROM 'users' WHERE mailing IS NOT NULL")
            mailing_id = self.cursor.fetchall()
        return mailing_id

    def del_user(self, user_id):
        with self.connection:
            self.cursor.execute("DELETE FROM 'users'"
                                "WHERE user_id = ?", (user_id,))

    def get_all_id(self):
        with self.connection:
            self.cursor.execute("SELECT user_id FROM 'users'")
            all_id = self.cursor.fetchall()
        return all_id
