from pymongo import MongoClient
import rapidjson


class MongoApi():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        guilds_settings = client.guilds.guilds_settings

    def get_guild(self, guild_id: int):
        guild_id = long(guild_id)

    def add_guild(self, guild_dict: dict):
        pass

    def check_one_param(self, guild_id: int, key):
        pass

    def check_guild_replays_channel(self, guild_id: int):
        pass

    def check_guild_stats_channel(self, guild_id: int, channel_id: int):
        pass
