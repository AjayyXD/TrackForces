import requests
import time 

def get_user_data(handle : str) : 
    try :
        time.sleep(1)
        data = requests.get(f"https://codeforces.com/api/user.info?handles={handle}&checkHistoricHandles=false")
        data_dict = data.json()
        if(data_dict["status"]=="OK"):
            final_data = {
                "handle" : data_dict["result"][0]["handle"],
                "rank" : data_dict["result"][0].get("rank","Unrated"),
                "rating" : data_dict["result"][0].get("rating",0)
            }
            return final_data
        else :
            raise Exception ("Codeforces did not respond for given username")
    except Exception as e :
        print(f"Some Error occured : {e}")
        return False
    
def get_user_submissions(handle : str) : 
    try :
        i = 1
        end = False
        final_data = {}
        time.sleep(1)
        while not end :  
            data = requests.get(f"https://codeforces.com/api/user.status?handle={handle}&from={i}&count={5000}")
            data_dict = data.json()
            if (data_dict["status"] == "OK") :
                count = 0
                for x in data_dict["result"]:
                    count = count + 1
                    final_data[x["id"]] = {
                        "id" : x["id"],
                        "contest_id" : x["problem"].get("contestId",0),
                        "index" : x["problem"].get("index",0),
                        "rating" : x["problem"].get("rating",0),
                        "tags" : x["problem"].get("tags",[]),
                        "verdict" : x.get("verdict",0)
                    }
                i = i + 5000
                if count < 5000 :
                    end = True
            else :
                raise Exception("Codeforces did not return data for given username")
        return final_data
    except Exception as e :
        print(e)
        return False

def update_user_submissions(handle,last_sub_id):
    try :
        i = 1
        end = False
        final_data = {}
        updated_last_sub_id = 0
        time.sleep(1)
        while not end :  
            data = requests.get(f"https://codeforces.com/api/user.status?handle={handle}&from={i}&count={5000}")
            data_dict = data.json()
            if (data_dict["status"] == "OK") :
                count = 0
                for x in data_dict["result"]:
                    if x["id"] == last_sub_id:
                        break
                    count = count + 1
                    if not updated_last_sub_id:
                        updated_last_sub_id = x["id"]
                    final_data[x["id"]] = {
                        "id" : x["id"],
                        "contest_id" : x["problem"].get("contestId",0),
                        "index" : x["problem"].get("index",0),
                        "rating" : x["problem"].get("rating",0),
                        "tags" : x["problem"].get("tags",[]),
                        "verdict" : x.get("verdict",0)
                    }
                i = i + 5000
                if count < 5000 :
                    end = True
            else :
                raise Exception("Codeforces did not return data for given username")
        return [final_data,updated_last_sub_id]
    except Exception as e :
        print(e)
        return False

            