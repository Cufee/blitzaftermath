import requests
import rapidjson
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

wg_player_medals_api_url_base = 'http://api.wotblitz.com/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='


# all_players = players.find()


# def divide_chunks(l, n):
#     # looping till length l
#     for i in range(0, len(l), n):
#         yield l[i:i + n]


# url = 'https://api.wotblitz.com/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='


# player_ids = players.find().distinct('player_id')

# requst_list = list(divide_chunks(player_ids, 90))

# for list_ in requst_list:
#     req_url = url + ','.join(str(p) for p in list_)
#     res = requests.get(req_url)

#     for player_ in list_:

#         res_j = rapidjson.loads(res.text)
#         data = res_j.get(
#             'data', {})
#         player_data = data.get(str(player_), {})

#         if not player_data:
#             continue
#         player_name = player_data.get(
#             'nickname', 'Unknown')

#         players.update_one({'player_id': player_}, {
#                            "$set": {'player_name': player_name}})
#         print(player_name)

# for player_ in all_players:
#     player_.update_one(player_, {'$set': {'aces': player_.get('aces_usa_5')}})

# all_clans = clans.find()

# for clan_ in all_clans:
#     clans.update_one(
#         clan_, {"$set": {'clan_aces': clan_.get('clan_aces_usa_5')}})
