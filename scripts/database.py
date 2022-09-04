import sqlite3


class Database:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id, group_id, sub_group):
        with self.connection:
            self.cursor.execute("INSERT INTO `users` (user_id, group_id, sub_group) VALUES (?, ?, ?)"
                                "ON CONFLICT (user_id) WHERE user_id = ? "
                                "DO UPDATE SET group_id = ?, sub_group = ?",
                                (user_id, group_id, sub_group, user_id, group_id, sub_group))

    def get_user(self, user_id):
        with self.connection:
            user_data = self.cursor.execute("SELECT group_id, sub_group FROM `users` WHERE user_id = ?",
                                            (user_id,)).fetchone()
        return user_data

    def get_all_id(self):
        with self.connection:
            self.cursor.execute("SELECT user_id FROM 'users'")
            all_id = self.cursor.fetchall()
        return all_id
