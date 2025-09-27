from models.database import Database
class Taxonomy():
    def __init__(self):
        database = Database('./databases/database.db')
        self.cursor, self.con = database.connect_db()
    def get_all_taxonomy(self):
        result= self.cursor.execute("SELECT * FROM taxonomy").fetchall()
        return result
    def read_ai_taxonomy(self, taxonomy_id):
        result = self.cursor.execute("SELECT * FROM taxonomy WHERE taxonomy_id=?", (taxonomy_id,)).fetchone()
        return dict(result)

    def average_taxonomy_calc(self, taxonomy_id):
        bloom_taxonomy = {
            "Onthouden": 1,
            "Begrijpen": 2,
            "Toepassen": 3,
            "Analyseren": 4,
            "Evalueren": 5,
            "Creëren": 6
        }

        result = self.cursor.execute("SELECT ai_taxonomy, teacher_taxonomy FROM taxonomy WHERE taxonomy_id=?", (taxonomy_id,)).fetchone()
        if result:
            ai_taxonomy, teacher_taxonomy = result
            if ai_taxonomy and teacher_taxonomy:
                ai_taxonomy_value = bloom_taxonomy.get(ai_taxonomy)
                teacher_taxonomy_value = bloom_taxonomy.get(teacher_taxonomy)
                average_taxonomy_value= round((ai_taxonomy_value + teacher_taxonomy_value) / 2)
                for key, value in bloom_taxonomy.items():
                    if value == average_taxonomy_value:
                        return key

    def update_taxonomy_average(self, taxonomy_id, average_taxonomy):
        self.cursor.execute("UPDATE taxonomy SET average_taxonomy = ? WHERE taxonomy_id = ?",(average_taxonomy, taxonomy_id))
        self.con.commit()
        return True

    def update_taxonomy(self,taxonomy_id, teacher_taxonomy):
        bloom_taxonomy = {
            "Onthouden": 1,
            "Begrijpen": 2,
            "Toepassen": 3,
            "Analyseren": 4,
            "Evalueren": 5,
            "Creëren": 6
        }
        if teacher_taxonomy not in bloom_taxonomy:
            raise ValueError(f"{teacher_taxonomy} is niet een geldige bloom taxonomie. Vul een geldige bloom taxonomie in.")
        self.cursor.execute("UPDATE taxonomy SET teacher_taxonomy =? WHERE taxonomy_id=?", (teacher_taxonomy,taxonomy_id))
        self.con.commit()
        return True

    def new_taxonomy(self):
        return niks
