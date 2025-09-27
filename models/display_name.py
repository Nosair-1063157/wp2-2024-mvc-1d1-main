from models.database import Database

class DisplayName():
    def __init__(self):
        database = Database('./databases/database.db')
        self.cursor, self.con = database.connect_db()

    def view_display_name(self,name, user_id):
        displayed_name = self.cursor.execute(
            "SELECT * FROM users WHERE display_name = ? AND user_id = ?",
            name
        ).fetchone()
        return displayed_name
