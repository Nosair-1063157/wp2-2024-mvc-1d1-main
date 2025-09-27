from models.database import Database
class Prompt():
    def __init__(self):
        database = Database('./databases/database.db')
        self.cursor, self.con = database.connect_db()

    def check_sorting(self, order):
        if order:
            if order.lower() in ['asc', 'desc']:
                return order
        return None
    
    def check_filter(self, param):
        valid_columns = ['prompt', 'prompt_title', 'user_id', 'questions_count', 'questions_correct', 'date_created']
        if param in valid_columns:
            return param 
        return None
        
    def get_query(self, order=None, order_param=None, user_id=None, count_only=False):
        if count_only:
            select_clause = "SELECT COUNT(*)"
        else:
            select_clause = """
                SELECT p.*, ROUND((p.questions_correct * 1.0 / NULLIF(p.questions_count, 0)) * 100, 2) AS percentage_correct,
                u.display_name
            """
            
        query = f"""
            {select_clause}
            FROM prompts p
            LEFT JOIN users u ON u.user_id = p.user_id
        """
        
        where_clauses = []
        if user_id:
            where_clauses.append(f"p.user_id = '{user_id}'")
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        if not count_only and order and order_param:
            query += f' ORDER BY {order_param} COLLATE NOCASE {order}'
            
        return query
            
            
    def read_prompts(self, order, order_param, user_id=None, page=1):
        per_page = 10
        offset = (page - 1) * per_page
        
        # Get total count
        count_query = self.get_query(order, order_param, user_id, count_only=True)
        total_count = self.cursor.execute(count_query).fetchone()[0]
        
        # Get paginated results
        query = self.get_query(order, order_param, user_id)
        query += f" LIMIT {per_page} OFFSET {offset}"
        
        results = self.cursor.execute(query).fetchall()
        return results, total_count
    
    def create_prompt(self, prompt, prompt_title, user_id, questions_count, questions_correct):
        try:
            if not prompt:
                raise ValueError("The 'prompt' field cannot be empty.")
            if not prompt_title:
                raise ValueError("The 'prompt_title' field cannot be empty.")
            self.cursor.execute(
                "INSERT INTO prompts (prompt, prompt_title, user_id, questions_count, questions_correct) VALUES (?,?,?,?,?)",
                (prompt, prompt_title, user_id, questions_count, questions_correct))
            self.con.commit()
            return True
        except Exception as e:
            print(f"Error: Couldn't add {e} to the database.")

    def get_prompt_by_id(self, prompt_id):
        self.cursor.execute("SELECT * FROM prompts WHERE prompts_id = ?", (prompt_id,))
        prompt = self.cursor.fetchone()
        return prompt

    def get_taxonomies_for_prompt(self, prompt_id):
        self.cursor.execute("""SELECT DISTINCT taxonomy_bloom FROM questions WHERE prompts_id = ?AND taxonomy_bloom IS NOT NULL""", (prompt_id,))
        taxonomies = self.cursor.fetchall()
        return [taxonomy['taxonomy_bloom'] for taxonomy in taxonomies]


    # Bron: https://launchschool.com/books/sql/read/joins
    def read_prompt(self, prompts_id):
        query = """
            SELECT 
                prompts.prompts_id,
                prompts.prompt,
                prompts.prompt_title,
                prompts.user_id,
                prompts.questions_count,
                prompts.questions_correct,
                prompts.date_created,
                users.display_name  
            FROM 
                prompts
            LEFT JOIN 
                users 
            ON 
                prompts.user_id = users.user_id
            WHERE 
                prompts.prompts_id = ?
        """
        result = self.cursor.execute(query, (prompts_id,)).fetchone()
        if result:
            return {
                'prompts_id': result[0],
                'prompt': result[1],
                'prompt_title': result[2],
                'user_id': result[3],
                'questions_count': result[4],
                'questions_correct': result[5],
                'date_created': result[6],
                'display_name': result[7]  
            }
        return None


    def calculate_incorrect(self, questions_count, questions_correct):
        if questions_correct > questions_count:
            raise ValueError("test")
        return questions_count - questions_correct

    def delete_prompt(self, prompts_id):
        self.cursor.execute("DELETE FROM prompts WHERE prompts_id=?", (prompts_id,))
        self.con.commit()
    
    

    def get_all_prompts(self):
        self.cursor.execute("SELECT * FROM prompts")
        return self.cursor.fetchall()



    def prompt_approving(self,prompts_id,action,question_json,question_id):
        try:
            if action == "approve":
                self.cursor.execute(""" UPDATE prompts
                                        SET questions_count = questions_count + 1,
                                        questions_correct = questions_correct + 1
                                        WHERE prompts_id = ?;""", (prompts_id,))
                self.cursor.execute(""" UPDATE questions
                                        SET question_json = ?
                                        WHERE questions_id = ?
                
                """,(question_json,question_id))

            elif action == "reject":
                self.cursor.execute(""" UPDATE prompts 
                                    SET questions_count = questions_count + 1 
                                    WHERE prompts_id = ?;""", (prompts_id,))
            self.con.commit()
            return True
        except Exception as e:
            print(f"Error: Couldn't retrieve {e}.")
            return False