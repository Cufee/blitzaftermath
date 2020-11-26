import rapidjson
import requests

class DiscordUsersApiV2():
    def __init__(self):
        self.API_URL = "https://api.aftermath.link/"

    def get_user_data(self, discord_user_id):
        '''Get user data from discord_id'''
        res_data = {}
        try:
            res = requests.get(f"{self.API_URL}users/{discord_user_id}")
            res_data = rapidjson.loads(res.text)
        except:
            raise Exception("It looks like Aftermath stats is partially down for maintenance.")

        if res_data.get("error"):
            if res_data.get("error") == "mongo: no documents in result":
                raise Exception("This user does not have a default WoT Blitz account set.")
            raise Exception(res_data.get("error"))

        return res_data

    def get_user_default_pid(self, discord_user_id):
        '''Get user data from discord_id'''
        res_data = {}
        try:
            res = requests.get(f"{self.API_URL}users/{discord_user_id}")
            res_data = rapidjson.loads(res.text)
        except:
            raise Exception("It looks like Aftermath stats is partially down for maintenance.")

        if res_data.get("error"):
            if res_data.get("error") == "mongo: no documents in result":
                raise Exception("This user does not have a default WoT Blitz account set.")
            raise Exception(res_data.get("error"))

        return res_data.get("player_id")

    def get_player_data(self, player_id):
        '''Get user data from player_id'''
        res_data = {}
        try:
            res = requests.get(f"{self.API_URL}players/{player_id}")
            res_data = rapidjson.loads(res.text)
        except:
            raise Exception("It looks like Aftermath stats is partially down for maintenance.")

        if res_data.get("error"):
            if res_data.get("error") == "mongo: no documents in result":
                raise Exception("Player not found.")
            raise Exception(res_data.get("error"))

        return res_data

    def set_user_player_id(self, discord_user_id, player_id):
        '''Update default player_id for user'''
        res_data = {}
        try:
            res = requests.patch(f"{self.API_URL}users/{discord_user_id}/newdef/{player_id}")
            res_data = rapidjson.loads(res.text)
        except:
            raise Exception("It looks like Aftermath stats is partially down for maintenance.")

        if res_data.get("error"):
            raise Exception(res_data.get("error"))
