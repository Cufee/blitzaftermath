from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

import rapidjson
import requests

from datetime import datetime, timedelta
from time import sleep

class ClanStatsApi():
    def __init__(self):
        mongo_uri = "mongodb://51.222.13.110:27017"
        client = MongoClient(mongo_uri)
        self.clans_collection = client.clan_activity.clans
        self.players_collection = client.clan_activity.players
    