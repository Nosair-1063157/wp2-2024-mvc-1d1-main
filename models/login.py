from models.database import Database
# Bron: https://blog.teclado.com/protecting-endpoints-in-flask-apps-by-requiring-login/
class Login():
    def __init__(self):
        database = Database('./databases/database.db')
        self.cursor, self.con = database.connect_db()
    
    def load_data(self, email, password):
        result = self.cursor.execute(
            "SELECT login, display_name, user_id, is_admin FROM users WHERE login = ? AND password = ?",
            (email, password)
        ).fetchone()

        if result:
            return {"login": result[0], "display_name": result[1], "user_id": result[2], "admin": (result[3])}
        return None
    
    # Bron: ChatGPT
    def load_data_by_email(self, email):
        # Haal alleen de gegevens van de gebruiker op basis van e-mail
        result = self.cursor.execute(
            "SELECT login, display_name, user_id, is_admin, password FROM users WHERE login = ?",
            (email,)
        ).fetchone()

        if result:
            return {
                "login": result[0],
                "display_name": result[1],
                "user_id": result[2],
                "admin": result[3],
                "hashed_password": result[4]
            }
        return None





