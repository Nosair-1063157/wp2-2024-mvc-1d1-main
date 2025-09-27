from models.database import Database

class Question:
    def __init__(self):
        database = Database('./databases/database.db')
        self.cursor, self.con = database.connect_db()

    def get_all_questions(self):
        result =self.cursor.execute("""
                SELECT * 
                FROM questions 
                """).fetchall()
        return result

    def read_questions(self, search_query=None, order="desc", user_id=None, page=1, per_page=10):
        try:
            offset = (page - 1) * per_page
            query = """
            SELECT * 
            FROM questions 
            WHERE 1=1
            """
            params = []
            if search_query:
                query += " AND question LIKE ?"
                params.append(f"%{search_query}%")
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            query += f" ORDER BY user_id {order.upper()} LIMIT ? OFFSET ?"
            params.extend([per_page, offset])
            self.cursor.execute(query, params)
            questions = self.cursor.fetchall()
            return questions
        except Exception as e:
            print(f"Error: {e}")
            return []


    def get_uncategorized_questions(self):
        query = """
        SELECT *
        FROM questions
        WHERE categorised = 0
    """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_total_questions(self, search_query=None, user_id=None):
        try:
            query = "SELECT COUNT(*) FROM questions WHERE 1=1"
            params = []
            
            if search_query:
                query += " AND question LIKE ?"
                params.append(f"%{search_query}%")
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return result[0]  
        except Exception as e:
            print(f"Error getting total questions: {e}")
            return 0

    def delete_question(self, question_id):
        self.cursor.execute("DELETE FROM questions WHERE questions_id = ?", (question_id,))
        self.con.commit()

    def create_question(self, questions_id, question, prompts_id, taxonomy_bloom, rtti, exported, user_id):
        try:
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO questions (questions_id, question, prompts_id, taxonomy_bloom, rtti, exported, user_id, date_created)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (questions_id if questions_id else None, question, prompts_id if prompts_id else None, taxonomy_bloom if taxonomy_bloom else None, rtti if rtti else None, exported, user_id)

            )
            self.con.commit()
        except Exception as e:
            print(f"Fout bij het uitvoeren van de query: {e}")

    def update_question(self, question_data):
        self.cursor.execute(
            """
            UPDATE questions 
            SET prompts_id = ?, user_id = ?, question = ?, taxonomy_bloom = ?, rtti = ?, exported = ? 
            WHERE questions_id = ?
            """,
            (
                question_data['prompts_id'],
                question_data['user_id'],
                question_data['question'],
                question_data['taxonomy_bloom'],
                question_data['rtti'],
                question_data['exported'],
                question_data['question_id']
            )
        )
        self.con.commit()


    def delete_question(self, question_id):
        self.cursor.execute("DELETE FROM questions WHERE questions_id = ?", (question_id,))
        self.con.commit()

    def get_question_by_id(self, question_id):
        self.cursor.execute("SELECT * FROM questions WHERE questions_id = ?", (question_id,))
        return self.cursor.fetchone()


    def category_approving(self,question_id,category,action):

        try:
            if action == "approve":

                self.cursor.execute(""" UPDATE questions
                                        SET taxonomy_bloom = ?, categorised = true
                                        WHERE questions_id = ?;""", (category,question_id,))
                self.con.commit()
            return True
        except Exception as e:
            print(f"Error: Couldn't retrieve {e}.")
            return False

    def rtti_approving(self,question_id,rtti,action):

        try:
            if action == "approve":
                self.cursor.execute(""" UPDATE questions
                                    SET rtti = ?, categorised = true
                                    WHERE questions_id = ?""",(rtti, question_id))
                self.con.commit()
        except Exception as e:
            print(f"Error: Couldn't retrieve {e}.")
            return False