import mariadb
import sys
from services import cf_client

class database_handler :
    def get_connection(self):
        try:
            conn = mariadb.connect(
                user="Ajay",
                password="123",
                host="127.0.0.1",
                port=3306,
                database="TrackForces"
            )
            return conn
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
    
    def insert_user_data(self,handle):
        conn = self.get_connection()
        cursor = conn.cursor()
        data = cf_client.get_user_data(handle)
        query = "INSERT INTO User (handle,rating) VALUES (?,?);"
        cursor.execute(query,(data["handle"],data["rating"]))
        conn.commit()
    
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