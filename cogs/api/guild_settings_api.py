import rapidjson
import requests

# API V2
from pymongo import MongoClient
from datetime import datetime, timezone


class Api():
    """Guild settings api using SQLite"""
    def __init__(self):
        self.API_URL_BASE = 'http://127.0.0.1:5000'

    def guild_get(self, guild_id, guild_name):
        url = self.API_URL_BASE + '/guild/' + guild_id
        res = requests.get(url)
        enabled_channels = []
        stats = []

        # If guild is not found, add it
        if res.status_code == 404:
            url = self.API_URL_BASE + '/guild'
            guild = {
                'guild_id': guild_id,
                'guild_name': guild_name
            }
            new_res = requests.post(url, json=guild)
        elif res.status_code == 200:
            new_res = res
        else:
            new_res = res
            return {"status_code": new_res.status_code}

        if new_res.status_code == 200:
            res_dict = rapidjson.loads(new_res.text)
            enabled_channels_res = res_dict.get('guild_channels_replays')
            guild_is_premium = res_dict.get('guild_is_premium')
            guild_name_cache = res_dict.get('guild_name')
            stats_res = res_dict.get('guild_render_fields')

            if enabled_channels_res:
                if ';' in enabled_channels_res:
                    enabled_channels = enabled_channels_res.split(';')
                else:
                    enabled_channels = [enabled_channels_res]
            if stats_res:
                if ';' in stats_res:
                    stats = stats_res.split(';')
                else:
                    stats = [stats_res]

            # Update guild name cache
            if guild_name_cache != guild_name:
                url = self.API_URL_BASE + '/guild/' + guild_id
                guild = {
                    'guild_name': guild_name
                }
                res = requests.put(url, json=guild)

            new_guild_obj = {
                "status_code": res.status_code,
                "enabled_channels": enabled_channels,
                "guild_is_premium": guild_is_premium,
                "stats": stats
            }

            return new_guild_obj

        else:
            return {"status_code": res.status_code}

    def guild_put(self, guild_id, dict):
        url = self.API_URL_BASE + '/guild/' + guild_id
        res = requests.get(url)
        if res.status_code != 200:
            return {"status_code": res.status_code}
        new_settings = {}
        dict_keys = dict.keys()
        for key in dict_keys:
            values = dict.get(key)
            if isinstance(values, list):
                values = ';'.join(values)
            new_settings[key] = values

        put_res = requests.put(url, json=new_settings)
        if put_res.status_code == 200:
            return True
        else:
            return {"status_code": put_res.status_code}


class API_v2():
    """Guild settings API using MongoDB"""
    def __init__(self):
        mongo_uri = "mongodb://51.222.13.110:27017"
        client = MongoClient(mongo_uri)
        self.guild_settings_collection = client.guilds.guilds_settings
        # features_collection = client.guilds.features      # Not used
    
    def get_all_guild_settings(self, guild_id: str):
        """Get all setting for a guild"""
        guild_settings = self.guild_settings_collection.find_one({"guild_id": guild_id})

        if guild_settings:
            status = 200
        else:
            status = 404
        return guild_settings, status

    def get_one_guild_setting(self, guild_id: str, key: str):
        """Get one guild setting from guild_id and key"""
        guild_settings = self.guild_settings_collection.find_one({"guild_id": guild_id})

        if guild_settings:
            setting = guild_settings.get(key)
            status = 200

        else:
            print("Guild not found")
            setting = None
            status = 404
        return setting, status

    def update_guild(self, guild_id: str, settings: dict, safe: bool = True):
        """Update settings for existing guild. By default, new settings keys must exist in old guild settings keys, this can be disabled with safe=False"""
        old_guild_settings = self.guild_settings_collection.find_one({"guild_id": guild_id})
        if not old_guild_settings:
            print(f"Guild {guild_id} not found.")
            return None, 404
            
        if set(settings.keys()).issubset(set(old_guild_settings.keys())) or not safe:
            new_settings = old_guild_settings.copy()
            new_settings.update(settings)
            self.guild_settings_collection.update_one(old_guild_settings, {"$set": new_settings}, upsert=False)
            return new_settings, 200
        else:
            print(f"Invalid settings. Please check if settings passed have the correct keys set or use safe=False to add new settings.")
            return None, 400

    def add_new_guild(self, guild_id: str, guild_name: str, guild_is_premium: bool = False):
        """Add new guild"""
        guild_settings = self.guild_settings_collection.find_one({"guild_id": guild_id})
        if guild_settings:
            return guild_settings, 409
        else:
            new_guild_settings = {
                "guild_id": guild_id,
                "guild_name": guild_name,
                "guild_is_premium": guild_is_premium,
                "guild_channels_replays": [],
                "guild_channels_stats": [],
            }
            result = self.guild_settings_collection.insert_one(new_guild_settings)

            if result.inserted_id:
                 return new_guild_settings, 200
            else:
                return None, 500