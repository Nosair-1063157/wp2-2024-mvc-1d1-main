from lib.gpt import bloom_taxonomy

from models.database import Database

class Category():

    def __init__(self):
        database = Database('./databases/database.db')
        self.cursor, self.con = database.connect_db()

    def categorise_question(self,questions,prompts):
        gpt = "presentatie"
        bloom_category = bloom_taxonomy.get_bloom_category(questions,prompts,gpt)
        return bloom_category

    def categorise_question_ollama(self,questions,prompts):
        gpt = "rac_test"
        bloom_category = bloom_taxonomy.get_bloom_category(questions,prompts,gpt)
        return bloom_category

    def get_selected_question(self, selected_question_id):
        query = """
                        SELECT 
                          question   
                        FROM 
                        questions
                        WHERE 
                        questions_id = ?
                    """
        result = self.cursor.execute(query,(selected_question_id,)).fetchone()
        return result["question"]


    def get_selected_prompt(self, selected_prompt_id):
        query = """
                        SELECT 
                          prompt   
                        FROM 
                        prompts
                        WHERE 
                        prompts_id = ?
                    """
        result = self.cursor.execute(query,(selected_prompt_id,)).fetchone()

        return result["prompt"]
    def get_selected_taxonomy(self, selected_taxonomy_id):
        query = """
                                SELECT 
                                  ai_taxonomy   
                                FROM 
                                taxonomy
                                WHERE 
                                taxonomy_id = ?
                            """
        result = self.cursor.execute(query, (selected_taxonomy_id,)).fetchone()
        return result["ai_taxonomy"]