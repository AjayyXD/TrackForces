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
                port=int(os.getenv("DB_PORT")),
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
        if result :
            return 1
        else :
            return 0
    
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
        query3 = "INSERT IGNORE INTO Category (name) VALUES (?);"
        query4 = "SELECT id FROM Category WHERE name = ?;"
        query5 = "INSERT IGNORE INTO Question_Categories (question_id, category_id) VALUES (?, ?);"
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
            for tags in data[x].get("tags",[]):
                cursor.execute(query3,(tags,))
                cursor.execute(query4,(tags,))
                category_id = cursor.fetchone()[0]
                cursor.execute(query5,(f"{data[x]["contest_id"]}{data[x]["index"]}",category_id))
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
        
        query1 = "INSERT IGNORE INTO Question (id,contest_id,problem_index,rating) VALUES (?,?,?,?)"
        query2 = "INSERT IGNORE INTO Submissions (submission_id,user_handle,question_id,verdict) VALUES (?,?,?,?)"
        query3 = "INSERT IGNORE INTO Category (name) VALUES (?);"
        query4 = "SELECT id FROM Category WHERE name = ?;"
        query5 = "INSERT IGNORE INTO Question_Categories (question_id, category_id) VALUES (?, ?);"
        query6 = "UPDATE User SET last_sub_id = ? WHERE handle = ?;"
        for x in submissions_data:
            cursor.execute(query1,(f"{submissions_data[x]["contest_id"]}{submissions_data[x]["index"]}",submissions_data[x]["contest_id"],submissions_data[x]["index"],submissions_data[x]["rating"]))
            cursor.execute(query2,(submissions_data[x]["id"],handle,f"{submissions_data[x]["contest_id"]}{submissions_data[x]["index"]}",submissions_data[x]["verdict"]))
            for tags in submissions_data[x].get("tags",[]):
                    cursor.execute(query3,(tags,))
                    cursor.execute(query4,(tags,))
                    category_id = cursor.fetchone()[0]
                    cursor.execute(query5,(f"{submissions_data[x]["contest_id"]}{submissions_data[x]["index"]}",category_id))
        cursor.execute(query6,(updated_last_sub_id,handle))
        conn.commit()
        conn.close()

    def get_user_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT handle,rating from User WHERE is_init = 1;"
        cursor.execute(query)
        user_data = cursor.fetchall()
        return user_data[0]
    
    def get_solved_stats(self,handle):
        conn = self.get_connection()
        cursor = conn.cursor()
        query1 = """SELECT 
            COUNT(*) as total_submissions,
            SUM(CASE WHEN verdict = 'OK' THEN 1 ELSE 0 END) as total_accepted_submissions
            FROM Submissions 
            WHERE user_handle = ?;"""
        query2 = """SELECT COUNT(DISTINCT question_id) as unique_solved
            FROM Submissions
            WHERE user_handle = ? AND verdict = 'OK';"""
        query3 = """SELECT COUNT(DISTINCT question_id) as unique_unsolved
            FROM Submissions
            WHERE user_handle = ? 
            AND question_id NOT IN (
            SELECT DISTINCT question_id 
            FROM Submissions 
            WHERE user_handle = ? AND verdict = 'OK');"""
        query4 = """SELECT ROUND(AVG(q.rating), 0) as avg_solved_rating
            FROM Question q
            JOIN Submissions s ON q.id = s.question_id
            WHERE s.user_handle = ? 
            AND s.verdict = 'OK' 
            AND q.rating > 0;"""
        query5 = """SELECT 
            q.rating,
            COUNT(DISTINCT s.question_id) as problems_solved
            FROM Question q
            JOIN Submissions s ON q.id = s.question_id
            WHERE s.user_handle = ? 
            AND s.verdict = 'OK' 
            AND q.rating > 0
            GROUP BY q.rating
            ORDER BY q.rating ASC;"""
        results = {
        "total_subs": 0,
        "total_solved_subs": 0,
        "unique_solved_qns": 0,
        "unique_unsolved_qns": 0,
        "avg_rating" : 0,
        }
        cursor.execute(query1,(handle,))
        result1 = cursor.fetchone()
        results["total_subs"] = result1[0]
        results["total_solved_subs"] = result1[1]
        cursor.execute(query2,(handle,))
        results2 = cursor.fetchone()
        results["unique_solved_qns"] = results2[0]
        cursor.execute(query3,(handle,handle))
        results3 = cursor.fetchone()
        results["unique_unsolved_qns"] = results3[0]
        cursor.execute(query4,(handle,))
        result4 = cursor.fetchone()
        results["avg_rating"] = int(result4[0])
        cursor.execute(query5,(handle,))
        result5 = cursor.fetchall()
        results["rating_distribution"] = result5


        return results
    
    def get_category_stats(self,handle):
        conn = self.get_connection()
        cursor = conn.cursor()
        query1 = """SELECT 
            c.name AS category_name,
            COUNT(DISTINCT s.question_id) AS unique_problems_solved
            FROM Submissions s
            JOIN Question_Categories qc ON s.question_id = qc.question_id
            JOIN Category c ON qc.category_id = c.id
            WHERE s.user_handle = ? 
            AND s.verdict = 'OK'
            GROUP BY c.id, c.name
            ORDER BY unique_problems_solved DESC;"""
        query2 = """SELECT 
            c.name AS category_name,
            COUNT(DISTINCT CASE WHEN s.verdict = 'OK' THEN s.question_id END) AS unique_solved,
            ROUND(
            (SUM(CASE WHEN s.verdict = 'OK' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 
            2
            ) AS submission_accuracy_percentage
            FROM Submissions s
            JOIN Question_Categories qc ON s.question_id = qc.question_id
            JOIN Category c ON qc.category_id = c.id
            WHERE s.user_handle = ?
            GROUP BY c.id, c.name
            ORDER BY submission_accuracy_percentage ASC; """
        cursor.execute(query1,(handle,))
        result1 = cursor.fetchall()
        cursor.execute(query2,(handle,))
        result2 = cursor.fetchall()
        result = {
            "category_wise_count" : result1,
            "category_wise_accuracy" : result2
        }
        return result
        




