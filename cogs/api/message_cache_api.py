from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError
import rapidjson
import requests

from datetime import datetime, timedelta
from time import sleep


class MessageCacheAPI():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.cache_collection = client.stats.message_cache

    def get_message_details(self, message_id: int, guild_id: int):
        query = {
            "_id": message_id,
            "guild_id": guild_id
        }
        cache_data = self.cache_collection.find_one(query)
        self.cache_collection.update_one(query, {"$set": {"timestamp": datetime.utcnow()}})
        return cache_data

    def get_messages_by_user(self, user_id: int, guild_id: int, seconds: int):
        query_timestamp = datetime.utcnow() - timedelta(seconds=seconds)
        query = {
            "user_id": user_id,
            "$and": [{"timestamp": {"$gt": query_timestamp}}, {"guild_id": guild_id}]
        }
        cache_data = self.cache_collection.find(query)
        return cache_data

    def cache_message(self, message_id: int, guild_id: int, user_id: int, request: dict):
        check = self.get_message_details(message_id, guild_id)
        if check:
            return

        cache_entry = {
            "_id": message_id,
            "guild_id": guild_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow(),
            "request": request
        }
        self.cache_collection.insert_one(cache_entry)
        return
        