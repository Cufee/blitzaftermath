import requests
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

client = MongoClient("mongodb://51.222.13.110:27017")
db = client.summer2020contest
glossary = client.summer2020contest

guilds = db.guilds
clans = db.clans
players = db.players
tanks = glossary.tanks
clan_marks = db.marksOfMastery

# all_players = players.find()

# for player_ in all_players:
#     players.update_one(player_, {"$set": {'aces_usa_5': player_.get('aces')}})

all_clans = clans.find()

for clan_ in all_clans:
    clans.update_one(
        clan_, {"$set": {'clan_aces_usa_5': 0}})
