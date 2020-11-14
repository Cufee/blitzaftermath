from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError
import rapidjson
import requests

from datetime import datetime, timedelta
from time import sleep


def get_wg_api_domain(realm=None, player_id=None):
    # Detect realm
    id_length = len(str(player_id))
    if realm:
        realm = realm.upper()

    if realm == 'RU' or id_length == 8:
        player_realm = 'RU'
        api_domain = 'http://api.wotblitz.ru'

    elif realm == 'EU' or id_length == 9:
        player_realm = 'EU'
        api_domain = 'http://api.wotblitz.eu'

    elif realm == 'NA' or id_length == 10:
        player_realm = 'NA'
        api_domain = 'http://api.wotblitz.com'

    else:
        print(player_id)
        raise Exception(
            f'{realm} is not a supported server.\nTry RU, EU or NA.')
    return api_domain, player_realm


def divide_chunks(list, n=99):
    # Split long list into chunks of N size
    for i in range(0, len(list), n):
        yield list[i:i + n]


class DiscordUsersApi():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.users_collection = client.stats.users

    def link_to_player(self, discord_user_id, player_id):
        '''Links Discord UserID to WG PlayerID in stats.users collection'''
        user_filter = {'_id': discord_user_id}
        user_data = {
            'default_player_id': player_id
        }
        self.users_collection.update_one(
            user_filter, {'$set': user_data}, upsert=True)
        return None

    def get_custom_bg(self, discord_user_id):
        '''Links Discord UserID to URL for a custom image bg'''
        user_filter = {'_id': discord_user_id}
        user_data = self.users_collection.find_one(user_filter)
        url = None
        if user_data:
            url = user_data.get('custom_bg', None)
        return url

    def add_custom_bg(self, discord_user_id, url):
        '''Links Discord UserID to URL for a custom image bg'''
        user_filter = {'_id': discord_user_id}
        user_data = {
            'custom_bg': url
        }
        self.users_collection.update_one(
            user_filter, {'$set': user_data}, upsert=True)
        return None

    def remove_custom_bg(self, discord_user_id):
        '''Links Discord UserID to URL for a custom image bg'''
        user_filter = {'_id': discord_user_id}
        user_data = {
            'custom_bg': None
        }
        self.users_collection.update_one(
            user_filter, {'$set': user_data}, upsert=True)
        return None

    def get_default_player_id(self, discord_user_id):
        user_filter = {'_id': discord_user_id}
        user_data = self.users_collection.find_one(
            user_filter)
        if user_data:
            return user_data.get('default_player_id', None)
        else:
            return None

class DiscordUsersApiV2():
    def __init__(self):
        self.API_URL = "http://158.69.62.236/"

    def get_user_data(self, discord_user_id):
        '''Get user data from discord_id'''
        res_data = {}
        try:
            res = requests.get(f"{self.API_URL}users/{discord_user_id}")
            res_data = rapidjson.loads(res.text)
        except:
            raise Exception("It looks like Aftermath stats is partially down for maintenance.")

        if res_data.get("error"):
            raise Exception(res_data.get("error"))

        return res_data

    def get_player_data(self, player_id):
        '''Get user data from player_id'''
        res_data = {}
        try:
            res = requests.get(f"{self.API_URL}players/{player_id}")
            res_data = rapidjson.loads(res.text)
        except:
            raise Exception("It looks like Aftermath stats is partially down for maintenance.")

        if res_data.get("error"):
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
