from pymongo import MongoClient
import rapidjson
import requests


def get_wg_api_domain(realm=None, player_id=None):
    # Detect realm
    id_length = len(str(player_id))
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
        raise Exception(
            'Unable to find this player on RU, EU or NA. ASIA server queries are not supported by WG.')
    return api_domainm, player_realm


def divide_chunks(list, n=99):
    # Split long list into chunks of N size
    for i in range(0, len(list), n):
        yield list[i:i + n]


class GuildApi():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.guilds_collection = client.guilds
        self.features = client.guilds.features
        self.guilds_settings = client.guilds.guilds_settings

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


class StatsApi():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.stats_collection = client.stats
        self.players = client.stats.players
        self.player_vehicles = client.stats.player_vehicles

        # WG Stats API URLs
        self.wg_api_all = '/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
        self.wg_api_vehicles = '/wotb/tanks/stats/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='

    def add_player(self, player_id: int):
        api_domain, realm = get_wg_api_domain(player_id=player_id)
        pass

    def get_all_stats(self, player_id):
        if type(player_id) == int:
            player_id_str_list = [str(player_id)]
        elif type(player_id) == list:
            player_ids_lists_raw = divide_chunks(player_id)
            player_id_str_list = []
            for list_ in player_ids_lists_raw:
                player_id_str_list.append(','.join(str(p) for p in list_))
        else:
            raise Exception('player_id needs to be a list or int')
            return

        all_player_data = {}
        for playeer_id_str in player_id_str_list:
            api_domain, realm = get_wg_api_domain(player_id=player_id)
            url = api_domain + self.wg_api_all + playeer_id_str
            res = requests.get(url)
            if res.status_code != 200:
                raise Exception(f'WG API responded with {res.status_code}')
                return
            player_list_data = rapidjson.loads(res.text).get('data', None)
            all_player_data.update(player_list_data)

        pass

    def get_detailed_stats(self, player_id: int):
        api_domain, realm = get_wg_api_domain(player_id=player_id)
        pass

    def get_vehicle_stats(self, player_id: int, tank_id: int):
        api_domain, realm = get_wg_api_domain(player_id=player_id)
        pass
