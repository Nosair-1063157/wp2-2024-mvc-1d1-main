from models.database import Database
import bcrypt


class Editor:

    def __init__(self):
        database = Database('./databases/database.db')
        self.cursor, self.con = database.connect_db()


    def view_editors(self):
        users = self.cursor.execute('SELECT * FROM users').fetchall()

        return users

    def create_editor(self, login, password, display_name, is_admin):
        try:
            existing_user = self.cursor.execute("SELECT user_id FROM users WHERE login = ?", (login,)).fetchone()
            if existing_user:
                raise ValueError("Login already exists. Please use a different login.")
            
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            if not login:
                return {"success": False, "message": "The 'login' field cannot be empty."}

            if not display_name:
                return {"success": False, "message": "The 'display_name' field cannot be empty."}
            if not password:
                return {"success": False, "message": "The 'password' field cannot be empty."}
            
            self.cursor.execute("INSERT INTO users (login, password, display_name, is_admin) VALUES (?, ?, ?, ?)", (login, hashed_password, display_name, is_admin))
            self.con.commit()
            return {"success": True, "message": "User created successfully"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred: {e}"}


        
    def edit_editor(self, user_id, display_name, password, login, is_admin):
        try:
            existing_user = self.cursor.execute("SELECT user_id FROM users WHERE login = ?", (login,)).fetchone()
            if existing_user:
                raise ValueError("Login already exists. Please use a different login.")
            
            if not user_id:
                raise ValueError("The 'user_id' field cannot be empty.")
            if not display_name:
                raise ValueError("The 'display_name' field cannot be empty.")
            if not login:
                raise ValueError("The 'login' field cannot be empty.")

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            self.cursor.execute(
                """
                UPDATE users
                SET display_name = ?, password = ?, login = ?, is_admin = ?
                WHERE user_id = ?
                """,
                (display_name, hashed_password, login, is_admin, user_id)
            )
            self.con.commit()
            return self.cursor.rowcount > 0
        except ValueError as ve:
            return {"success": False, "message": str(ve)}


    def delete_editor(self, user_id):
        try:
            self.cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            self.con.commit()
        except Exception as e:
            print(f"Error: {e}")
            print(f"Error in deleting editor {user_id}: {e}")

            return False

    def read_editor(self, user_id):
        self.cursor.execute(
            "SELECT user_id, login, password, display_name, is_admin "
            "FROM users "
            "WHERE user_id = ?",
        (user_id,)
        )
        user = self.cursor.fetchone()

        if user:
            return {
            "user_id": user[0],
            "login": user[1],
            "password": user[2],
            "display_name": user[3],
            "is_admin": bool(user[4]),
            }

        else:
            return None
    
    def view_editors(self, page=1, per_page=10, search_name=None, search_login=None, filter_admin=None, sort_name=None):
        offset = (page - 1) * per_page

        query = "SELECT * FROM users WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM users WHERE 1=1"
        params = []
        count_params = []

        # Filters
        if search_name:
            query += " AND display_name LIKE ?"
            count_query += " AND display_name LIKE ?"
            params.append(f"%{search_name}%")
            count_params.append(f"%{search_name}%")
        
        if search_login:
            query += " AND login LIKE ?"
            count_query += " AND login LIKE ?"
            params.append(f"%{search_login}%")
            count_params.append(f"%{search_login}%")

        if filter_admin in ['0', '1']:
            query += " AND is_admin = ?"
            count_query += " AND is_admin = ?"
            params.append(filter_admin)
            count_params.append(filter_admin)

            # Sorting
        if sort_name == "asc":
            query += " ORDER BY display_name ASC"
        elif sort_name == "desc":
            query += " ORDER BY display_name DESC"

        # Pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        # Execute main query
        users = self.cursor.execute(query, params).fetchall()

        # Execute count query
        total_count = self.cursor.execute(count_query, count_params).fetchone()[0]

        return users, total_count
