import sys
from database import db
class stats_handler:
    def __init__(self):
        self.database_handler = db.database_handler()

    def general_stats(self,handle):
        data = self.database_handler.get_solved_stats(handle)
        data["solved_subs_percentage"] = (int(data["total_solved_subs"])/int(data["total_subs"]))*100.0
        data["solved_qns_percentage"] = (int(data["unique_solved_qns"]))/(int(data["unique_unsolved_qns"])+int(data["unique_solved_qns"]))*100.0
        return data
    
    def category_stats(self,handle):
        data = self.database_handler.get_category_stats(handle)
        return data

    def get_user_stats(self):
        user_data = self.database_handler.get_user_data()
        self.database_handler.update_fill_submission(user_data[0])
        general_stats = self.general_stats(user_data[0])
        category_stats = self.category_stats(user_data[0])
        stats = {
            "handle" : user_data[0],
            "rating" : int(user_data[1]),
            "general_stats" : general_stats,
            "category_stats" : category_stats
        }
        return stats
    
        
    
