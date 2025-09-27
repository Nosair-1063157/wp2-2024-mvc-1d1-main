import json
import os
import sqlite3


class JSONExporter:



    def get_all_questions_json(self):
        conn = sqlite3.connect('databases/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT question_json FROM questions WHERE question_json IS NOT NULL")
        result = cursor.fetchall()
        json_data =[json.loads(row[0]) for row in result if row[0]]
        return json.dumps(json_data, indent=4, ensure_ascii=False)

    def get_question_json(self, question_id):
        conn = sqlite3.connect('databases/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT question_json FROM questions WHERE questions_id = ? and categorised = true", (question_id,))

        result = cursor.fetchone()

        if result and result[0]:
            try:
                json_data = json.loads(result[0])
                return json.dumps(json_data, indent=4, ensure_ascii=False)
            except json.JSONDecodeError:
                return  None
        return None


    def convert_string_to_json(self):
        try:
            file_name = "../json_dummy.txt"
            with open(file_name, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            return json_data

        except FileNotFoundError:
            return "Error: Bestand niet gevonden"

        except json.JSONDecodeError:
            return "Error: Ongeldig JSON-formaat in bestand"

        except Exception as error:
            return f"Error: {str(error)}"

    def save_to_json(self, output_file = "output.json"):
        json_data = self.convert_string_to_json()
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(json_data, file)




converter = JSONExporter()

json_result = converter.save_to_json("output.json")




