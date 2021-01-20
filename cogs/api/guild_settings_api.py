# API V2
from pymongo import MongoClient


class API_v2():
    """Guild settings API using MongoDB"""
    def __init__(self):
        mongo_uri = "mongodb://51.222.13.110:27017"
        client = MongoClient(mongo_uri)
        self.guild_settings_collection = client.guilds.guilds_settings
        # features_collection = client.guilds.features      # Not used
    
    def get_all_guilds(self):
        """Get all setting for all guilds"""
        guild_settings = self.guild_settings_collection.find()

        if guild_settings:
            status = 200
        else:
            status = 404
        return guild_settings, status
    
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