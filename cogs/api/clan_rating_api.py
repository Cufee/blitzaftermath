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


class ClansRating():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.clans_collection = client.stats.clans

    def get_top_n(self, realm: str, metric: str = "total_points", n: int = 5):
        """Retrieves n clans from DB usig the metric("total_points" by default) on a set realm."""
        realm_upper = realm.upper()
        clans_filter = {"realm": realm_upper}
        clans_selector = self.clans_collection.find(clans_filter).sort(metric, -1).limit(n)
        clans_list = list(clans_selector)
        if not clans_list:
            raise Exception(f"No clans found on {realm_upper} when sorting by {metric}")

        return clans_list

    def get_clan_details(self, realm: str, clan_tag: str):
        """Retrieve info of a specific clan using realm and clan_tag"""
        realm_upper, clan_tag_upper = realm.upper(), clan_tag.upper()
        clans_filter = {"realm": realm_upper, "tag": clan_tag_upper}
        clan_data = self.clans_collection.find_one(clans_filter)
        if not clan_data:
            raise Exception(f"{clan_tag_upper} not found on {realm_upper}")

        return clan_data

    def add_clan(self, realm: str, clan_id: int = None, clan_tag: str = None):
        """Add a clan to DB by clan id or clan tag and realm"""
        realm_upper = realm.upper()
        api_domain = get_wg_api_domain(realm=realm)
        if not clan_id and not clan_tag:
            raise Exception("No clan tag or id provided")
        elif not clan_id and clan_tag:
            # Get clan id from clan tag
            clan_tag_upper = clan_tag.upper()
            clan_search_base = "https://api.wotblitz.com/wotb/clans/list/?application_id=add73e99679dd4b7d1ed7218fe0be448&fields=clan_id,tag&search="
            search_url = api_domain + clan_search_base + str(clan_tag_upper)
            search_res = requests.get(search_url)
            if search_res.status_code != 200:
                raise Exception(f"WG API responded with {search_res.status_code}")

            search_data = rapidjson.loads(search_res.text).get("data")
            for clan_snip in search_data:
                if clan_snip.get("tag") == clan_tag_upper:
                    clan_id = clan_snip.get("clan_id")
            
            if not clan_id:
                raise Exception(f"{clan_tag_upper} not found on {realm_upper}")

        else:
            # clan_id is provided
            pass

        clans_api_base = "/wotb/clans/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&extra=members&clan_id="
        full_url = api_domain + clans_api_base + str(clan_id)
        clan_data_res = requests.get(full_url)
        if clan_data_res.status_code != 200:
            raise Exception(f"WG API responded with {clan_data_res.status_code}")

        clan_data = rapidjson.loads(clan_data_res.text).get("data", {}).get(str(clan_id))
        if not clan_data or clan_data.get("is_clan_disbanded"):
            raise Exception("Invalid clan id provided.")

        self.clans_collection.update_one({"_id": clan_id}, {"$set": clan_data}, upsert=True)

