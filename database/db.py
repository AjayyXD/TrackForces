import mariadb
import sys
from services import cf_client
import os
from dotenv import load_dotenv

load_dotenv()

class database_handler :
    def get_connection(self):
        try:
            conn = mariadb.connect(
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME")
            )
            return conn
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
    
    def insert_user_data(self,data):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO User (handle,rating,last_sub_id,is_init) VALUES (?,?,?,1);"
        cursor.execute(query,(data["handle"],data["rating"],data["last_sub_id"]))
        conn.commit()
        conn.close()
    
    def is_init(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT is_init FROM User;"
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0]
    
    def last_recorded_submission(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT last_sub_id FROM User;"
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0]
    
    def init_fill_submission(self,handle):
        conn = self.get_connection()
        cursor = conn.cursor()
        data = cf_client.get_user_submissions(handle)
        user_data = cf_client.get_user_data(handle)
        first = 0
        query1 = "INSERT IGNORE INTO Question (id,contest_id,problem_index,rating) VALUES (?,?,?,?)"
        query2 = "INSERT IGNORE INTO Submissions (submission_id,user_handle,question_id,verdict) VALUES (?,?,?,?)"
        for x in data:
            if not first :
                first = data[x]["id"]
                user_data["last_sub_id"] = first
                user_data["handle"] = handle
                self.insert_user_data(user_data)
            cursor.execute(query1,(f"{data[x]["contest_id"]}{data[x]["index"]}",data[x]["contest_id"],data[x]["index"],data[x]["rating"]))
            conn.commit()
            cursor.execute(query2,(data[x]["id"],handle,f"{data[x]["contest_id"]}{data[x]["index"]}",data[x]["verdict"]))
            conn.commit()
    
    def update_last_sub_id(self,handle,updated_last_sub_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "UPDATE User SET last_sub_id = ? WHERE handle = ?;"
        cursor.execute(query,(updated_last_sub_id,handle))
        conn.commit()
        conn.close()
    
    def update_fill_submission(self,handle):
        conn = self.get_connection()
        cursor = conn.cursor()
        query0 = "SELECT last_sub_id FROM User WHERE handle = ? ;"
        cursor.execute(query0,(handle,))
        last_sub_id = cursor.fetchone()
        complete_data = cf_client.update_user_submissions(handle,last_sub_id[0])
        submissions_data = complete_data[0]
        updated_last_sub_id = complete_data[1]
        self.update_last_sub_id(handle,updated_last_sub_id)
        query1 = "INSERT IGNORE INTO Question (id,contest_id,problem_index,rating) VALUES (?,?,?,?)"
        query2 = "INSERT IGNORE INTO Submissions (submission_id,user_handle,question_id,verdict) VALUES (?,?,?,?)"
        for x in submissions_data:
            cursor.execute(query1,(f"{submissions_data[x]["contest_id"]}{submissions_data[x]["index"]}",submissions_data[x]["contest_id"],submissions_data[x]["index"],submissions_data[x]["rating"]))
            cursor.execute(query2,(submissions_data[x]["id"],handle,f"{submissions_data[x]["contest_id"]}{submissions_data[x]["index"]}",submissions_data[x]["verdict"]))
        conn.commit()
        conn.close()

