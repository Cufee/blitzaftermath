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


class StatsApi():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.stats_collection = client.stats
        self.players = client.stats.players
        self.sessions = client.stats.sessions
        self.clans = client.stats.clans
        self.glossary = client.glossary.tanks
        self.glossary_averages = client.glossary.tankaverages

        # WG Stats API URLs
        self.wg_api_personal_data = '/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
        self.wg_api_clan_info = '/wotb/clans/accountinfo/?application_id=add73e99679dd4b7d1ed7218fe0be448&extra=clan&account_id='
        self.wg_api_achievements = '/wotb/account/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
        self.wg_api_statistics_all = '/wotb/account/info/?application_id=add73e99679dd4b7d1ed7218fe0be448&extra=statistics.rating&fields=statistics.rating,statistics.all,updated_at,last_battle_time&account_id='
        self.wg_api_vehicle_statistics = '/wotb/tanks/stats/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='
        self.wg_api_vehicle_achievements = '/wotb/tanks/achievements/?application_id=add73e99679dd4b7d1ed7218fe0be448&account_id='

    def list_to_chunks(self, lst: list, chunk_size: int):
        """Return list broken up into chunk_size-sized lists from lst."""
        fixed_list = []
        for i in range(0, len(lst), chunk_size):
            fixed_list.append(lst[i:i + chunk_size])
        print(len(fixed_list), len(fixed_list[-1]))
        return fixed_list

    def update_players(self, player_ids_long: list, realm=None):
        """Takes in a list of player ids and realm (optional). Adds/Updates all players to the database with default settings.\nDoes not cache any stats."""
        if len(player_ids_long) > 100:
            player_ids_list = self.list_to_chunks(
                lst=player_ids_long, chunk_size=99)
        else:
            player_ids_list = [player_ids_long]

        # Get API domain through passed realm or first player_id on the list
        if realm:
            api_domain, _ = get_wg_api_domain(realm=realm)
        else:
            api_domain, realm = get_wg_api_domain(
                player_id=player_ids_list[0][0])

        players_updated = 0
        new_players_list = []
        for player_ids in player_ids_list:
            # Count requests send to avoid spam / Not implemented
            requests_ctn = 0
            # Create a string from player IDs
            player_list_str = ','.join(str(p) for p in player_ids)
            url_players = api_domain + self.wg_api_personal_data + player_list_str
            url_player_clans = api_domain + self.wg_api_clan_info + player_list_str
            res_players = requests.get(url_players)
            res_player_clans = requests.get(url_player_clans)
            requests_ctn += 2

            res_player_data_raw = rapidjson.loads(res_players.text)
            res_player_clans_raw = rapidjson.loads(res_player_clans.text)
            if res_players.status_code != 200 or res_player_clans.status_code != 200:
                raise Exception(
                    f'WG API returned:\nPlayer data:{res_players.status_code}\nClan data:{res_player_clans.status_code}')
            elif not res_player_data_raw.get('data') or not res_player_clans_raw.get('data'):
                raise Exception(f'WG API did not return any data')

            res_player_data = res_player_data_raw.get('data')
            res_player_clans_data = res_player_clans_raw.get('data')

            for player_id in player_ids:
                # Get player details and premium status
                player_details = self.players.find_one({'_id': player_id})
                update_premium = True
                if player_details:
                    update_premium = False

                player_data = res_player_data.get(str(player_id))
                player_clan_data = res_player_clans_data.get(
                    str(player_id)) or {}

                if not player_data:
                    print(player_data)
                    print(f'No data, skipping {player_id}')
                    continue

                # Player info
                nickname = player_data.get('nickname')
                last_battle_time = datetime.utcfromtimestamp(
                    player_data.get('last_battle_time'))

                new_player = {}

                # Detailed clan info
                clan_data = player_clan_data.get('clan')
                if clan_data:
                    clan_name = clan_data.get('name')
                    clan_tag = clan_data.get('tag')
                    clan_id = player_clan_data.get('clan_id')
                    clan_role = player_clan_data.get('role')
                    clan_joined_at = datetime.utcfromtimestamp(
                        player_clan_data.get('joined_at'))

                    new_player.update({
                        'clan_id': clan_id,
                        'clan_name': clan_name,
                        'clan_tag': clan_tag,
                        'clan_role': clan_role,
                        'clan_joined_at': clan_joined_at
                    })

                new_player.update({
                    'nickname': nickname,
                    'realm': realm,
                    'last_battle_time': last_battle_time,
                })

                if update_premium:
                    new_player.update(
                        {'am_premium_expiration': (datetime.utcnow() + timedelta(days=7))})

                new_players_list.append(UpdateOne({'_id': player_id}, {
                                        '$set': new_player}, upsert=True))

                players_updated += 1

        try:
            if new_players_list:
                result_players = self.players.bulk_write(
                    new_players_list, ordered=False)
                print(f'{datetime.utcnow()}\n{result_players.bulk_api_result}')
                return (f'Done, updated {players_updated} players')
            else:
                print(f'{datetime.utcnow()}\nNo valid objects to insert.')
                return None
        except Exception as e:
            if e == BulkWriteError:
                print(e.details)
            else:
                print(e)
            return None

    def update_stats(self, player_ids_long: list, realm=None, hard=False):
        """Takes in a list of player ids and realm (optional). Updates stats for each player"""
        if len(player_ids_long) > 100:
            player_ids_list = self.list_to_chunks(
                lst=player_ids_long, chunk_size=99)
        else:
            player_ids_list = [player_ids_long]

        # Get API domain through passed realm or first player_id on the list
        if realm:
            api_domain, _ = get_wg_api_domain(realm=realm)
        else:
            api_domain, _ = get_wg_api_domain(player_id=player_ids_list[0][0])

        sessions_list = []
        for player_ids in player_ids_list:
            # Count requests send to avoid spam
            requests_ctn = 0
            # Create a string from player IDs
            player_list_str = ','.join(str(p) for p in player_ids)
            url_stats_all = api_domain + self.wg_api_statistics_all + player_list_str
            res_stats_all = requests.get(url_stats_all)
            requests_ctn += 1

            res_stats_all_raw = rapidjson.loads(res_stats_all.text)
            if res_stats_all.status_code != 200:
                raise Exception(
                    f'WG API returned {res_stats_all.status_code}')
            elif not res_stats_all_raw:
                raise Exception(f'WG API did not return any data')
            res_stats_all_data = res_stats_all_raw.get('data')

            for player_id in player_ids:
                # Get player details and premium status
                player_details = self.players.find_one({'_id': player_id})
                if not player_details:
                    print(f'Player {player_id} not in DB, skipping')
                    continue

                # Get last player data and sessions
                last_session_list = list(self.sessions.find(
                    {'player_id': player_id}).sort('timestamp', -1).limit(1))
                if last_session_list:
                    last_session = last_session_list[0]
                else:
                    last_session = {}

                last_battles_random = last_session.get('battles_random', 0)
                # last_battles_rating = last_session.get('battles_rating', 0)
                # last_battles_total = last_battles_random + last_battles_rating

                player_data = res_stats_all_data.get(str(player_id))
                if not player_data:
                    print(f'No data for {player_id}')
                    continue
                stats_random = player_data.get('statistics', {}).get('all', {})
                battles_random = player_data.get(
                    'statistics', {}).get('all', {}).get('battles', 0)
                stats_rating = player_data.get(
                    'statistics', {}).get('rating', {})
                battles_rating = player_data.get('statistics', {}).get(
                    'rating', {}).get('battles', 0)
                last_battle_time = datetime.utcfromtimestamp(
                    player_data.get('last_battle_time'))
                # battles_total = battles_random + battles_rating

                # Checking self.hard to allow force resets
                if last_battles_random == battles_random and battles_random != 0 and not hard:
                    print(f'Player {player_id} played 0 battles')
                    continue

                # Gather per vehicle stats
                vehicle_stats_url = api_domain + \
                    self.wg_api_vehicle_statistics + str(player_id)
                vehicles_stats_res = requests.get(vehicle_stats_url)
                requests_ctn += 1
                vehicles_stats_raw = rapidjson.loads(
                    vehicles_stats_res.text)
                if vehicles_stats_res.status_code != 200 or not vehicles_stats_raw:
                    raise Exception(
                        f'Failed to get data from WG API, status code {vehicles_stats_res.status_code}')
                vehicles_stats_data = vehicles_stats_raw.get(
                    'data').get(str(player_id))
                vehicles_stats = {}
                for tank_stats in vehicles_stats_data:
                    tank_id = tank_stats.get('tank_id')
                    vehicles_stats.update({str(tank_id): tank_stats})

                player_stats = {
                    'player_id': player_id,
                    'timestamp': datetime.utcnow(),
                    'stats_random': stats_random,
                    'battles_random': battles_random,
                    'stats_rating': stats_rating,
                    'battles_rating': battles_rating,
                    'last_battle_time': last_battle_time,
                    'archive': False,
                    'vehicles': vehicles_stats
                }
                sessions_list.append(InsertOne(player_stats))

                if requests_ctn % 100 == 0:
                    sleep(5)

        try:
            if sessions_list:
                result = self.sessions.bulk_write(
                    sessions_list, ordered=False)
                print(f'{datetime.utcnow()}\n{result.bulk_api_result}')
                return 'Done'
            else:
                print(f'{datetime.utcnow()}\nNo valid objects to insert.')
                return None
        except Exception as e:
            if e == BulkWriteError:
                print(e.details)
            else:
                print(e)
            return None

    def add_premium_time(self, player_id: int, days_to_add=None):
        player_details = self.players.find_one({'_id': player_id})
        if not player_details or not days_to_add:
            raise Exception(
                f'Player with ID {player_id} not found or days_to_add is 0')

        current_expiration = player_details.get(
            'am_premium_expiration') or datetime.utcnow()
        new_expiration = current_expiration + timedelta(days=days_to_add)
        player_update = {
            'am_premium_expiration': new_expiration
        }
        self.players.update_one(player_details, {'$set': player_update})

    def get_session_stats(self, player_id: int, session_duration: datetime = None):
        """Get a dict of the session specified. Where session_duration is a datetime obj (timedelta), will default to last session vs current stats."""
        player_details = self.players.find_one({'_id': player_id})
        if not player_details:
            raise Exception(f'Player with ID {player_id} not found')

        # Request and check basic stats
        api_domain, _ = get_wg_api_domain(player_id=player_id)
        stats_all_url = api_domain + \
            self.wg_api_statistics_all + str(player_id)
        url_player_clans = api_domain + self.wg_api_clan_info + str(player_id)

        stats_all_res = requests.get(stats_all_url)
        stats_all_res_raw = rapidjson.loads(stats_all_res.text)

        res_player_clans = requests.get(url_player_clans)
        player_clans_raw = rapidjson.loads(res_player_clans.text)

        if stats_all_res.status_code != 200 or not stats_all_res_raw or not player_clans_raw:
            raise Exception(
                f'Failed to get player stats, WG responded with {stats_all_res.status_code}')

        # Check Basic stats
        player_data = stats_all_res_raw.get('data').get(str(player_id))
        player_clan_data = player_clans_raw.get(
            'data').get(str(player_id), {}).get('clan')

        # Update clan data if needed
        if player_clan_data and player_details.get("clan_tag") != player_clan_data.get("tag"):
            player_clan_role = player_clans_raw.get(
                'data').get(str(player_id)).get("role")
            player_clan_joined_at = datetime.utcfromtimestamp(player_clans_raw.get(
                'data').get(str(player_id)).get("joined_at"))

            clan_update = {
                "clan_id": player_clan_data.get("clan_id"),
                "clan_joined_at": player_clan_joined_at,
                "clan_name": player_clan_data.get("name"),
                "clan_role": player_clan_role,
                "clan_tag": player_clan_data.get("tag")
            }
            self.players.update_one(
                player_details, {"$set": clan_update}, upsert=False)
            player_details.update(clan_update)

        stats_random = player_data.get('statistics', {}).get('all', {})
        stats_rating = player_data.get('statistics', {}).get('rating', {})

        if session_duration:
            # No code to check Rating mode atm
            # last_stats_list = list(self.sessions.find({'player_id': player_id, '$or': [{'stats_random': {'$exists': True, '$ne': stats_random}}, {
            #                        'stats_rating': {'$exists': True, '$ne': stats_rating}}], 'timestamp': {'$gt': session_duration}}).sort('timestamp', 1).limit(1))
            last_stats = self.sessions.find_one({'player_id': player_id, 'stats_random': {
                '$ne': stats_random}, 'timestamp': {'$gt': session_duration}}, sort=[('timestamp', 1)])
        else:
            # No code to check Rating mode atm
            # last_stats_list = list(self.sessions.find({'player_id': player_id, '$or': [{'stats_random': {'$exists': True, '$ne': stats_random}}, {
            last_stats = self.sessions.find_one({'player_id': player_id, 'stats_random': {
                '$ne': stats_random}}, sort=[('timestamp', -1)])

        # Compare stats
        if last_stats:
            random_diff = {key: (stats_random.get(key, 0) - last_stats.get('stats_random').get(
                key, 0)) for key in stats_random.keys()}
            rating_diff = {key: (stats_rating.get(key, 0) - last_stats.get('stats_rating').get(
                key, 0)) for key in stats_rating.keys()}

            session_all = {
                'stats_random': random_diff,
                'stats_rating': rating_diff,
                'timestamp': last_stats.get('timestamp')
            }
        else:
            result = self.update_stats(player_ids_long=[player_id])
            print(result)
            if result:
                raise Exception(
                    'I just refreshed your session, please try again.')
            else:
                raise Exception(
                    'Not enough data. I tried to refresh your session, but you did not play a single regular battle yet.')

        live_stats_all = {
            'live_stats_random': stats_random,
            'live_stats_rating': stats_rating,
        }

        # Request and check detailed stats
        stats_detailed_url = api_domain + \
            self.wg_api_vehicle_statistics + str(player_id)
        stats_detailed_res = requests.get(stats_detailed_url)
        stats_detailed_res_raw = rapidjson.loads(stats_detailed_res.text)

        if stats_detailed_res.status_code != 200 or not stats_detailed_res_raw:
            print(
                f'Failed to get detailed player stats, WG responded with {stats_detailed_res.status_code}')
            session_detailed = {}
        else:
            # Get current detailed stats
            # Sort dict by last played battle
            stats_detailed_tanks = sorted(stats_detailed_res_raw.get(
                'data').get(str(player_id)), key=lambda x: x['last_battle_time'], reverse=True)
            stats_detailed_data = {}
            for tank_stats in stats_detailed_tanks:
                tank_id = tank_stats.get('tank_id')
                tank_stats_all = tank_stats
                stats_detailed_data.update({str(tank_id): tank_stats_all})

            # Get last session object
            last_detailed_stats_data = last_stats.get('vehicles')
            session_detailed = {}
            # Limiting detailed stats to 10 tanks to avoid running out of memory
            tank_count = 0
            for tank in stats_detailed_data.keys():
                session_old = last_detailed_stats_data.get(
                    tank, {}).get('all')
                session_current = stats_detailed_data.get(
                    tank, {}).get('all')

                if session_old:
                    diff = {key: (session_current.get(key) - session_old.get(
                        key)) for key in session_current.keys()}
                else:
                    diff = session_current

                if diff.get('battles') != 0 and tank_count < 10:
                    tank_glossary = self.glossary.find_one(
                        {'tank_id': int(tank)}) or {}
                    tank_name = tank_glossary.get('name') or 'Unknown'
                    tank_tier = tank_glossary.get('tier') or 0
                    tank_nation = tank_glossary.get(
                        'nation') or 'other'
                    tank_id = tank_glossary.get('tank_id') or 0

                    tank_data = {
                        'tank_name': tank_name,
                        'tank_tier': tank_tier,
                        'tank_nation': tank_nation,
                        'tank_id': tank_id
                    }
                    diff.update(tank_data)
                    diff = self.add_vehicle_wn8(diff)
                    session_detailed.update({tank: diff})
                    tank_count += 1

        return player_details, live_stats_all, session_all, session_detailed

    def get_vehicle_stats(self, player_id: int, tank_id: int, timestamp: datetime = None):
        query_params = {'player_id': player_id}
        if timestamp:
            query_params.update({'timestamp': {'$lt': timestamp}})
        session_stats = self.sessions.find(query_params).sort(
            'timestamp', -1).limit(1).distinct(f'vehicles.{tank_id}.all')
        if not session_stats:
            return None
        else:
            session_stats = session_stats[0]
            return(session_stats)

    def add_vehicle_wn8(self, tank_data: dict):
        tank_battles = tank_data.get("battles", 0)
        if tank_battles == 0 or not tank_battles:
            print('Tank has 0 battles')
            return tank_data
        tank_id = int(tank_data.get('tank_id', 0))
        tank_averages = self.glossary_averages.find_one(
            {'tank_id': tank_id}) or None
        if not tank_averages or not tank_averages.get('meanSd'):
            # print(f'Missing data for tank {tank_id}')
            return tank_data

        # Expected values
        exp_dmg = tank_averages.get('special', {}).get('damagePerBattle')
        exp_spott = tank_averages.get('special', {}).get('spotsPerBattle')
        exp_frag = tank_averages.get('special', {}).get('killsPerBattle')
        exp_def = (tank_averages.get('all').get(
            'dropped_capture_points') / tank_averages.get('all').get('battles'))
        exp_wr = tank_averages.get('special', {}).get('winrate')
        # Organize data
        tank_avg_wr = (tank_data.get("wins") / tank_battles) * 100
        tank_avg_dmg = tank_data.get(
            'damage_dealt', 0) / tank_battles
        tank_avg_spott = tank_data.get('spotted', 0) / tank_battles
        tank_avg_frag = tank_data.get('frags', 0) / tank_battles
        tank_avg_def = tank_data.get(
            'dropped_capture_points', 0) / tank_battles

        # Calculate WN8 metrics
        rDMG = tank_avg_dmg / exp_dmg
        rSPOTT = tank_avg_spott / exp_spott
        rFRAG = tank_avg_frag / exp_frag
        rDEF = tank_avg_def / exp_def
        rWR = tank_avg_wr / exp_wr

        rWRc = max(0, ((rWR - 0.71) / (1 - 0.71)))
        rDMGc = max(0, ((rDMG - 0.22) / (1 - 0.22)))
        rFRAGc = max(0, (min(rDMGc + 0.2, (rFRAG - 0.12) / (1 - 0.12))))
        rSPOTTc = max(0, (min(rDMGc + 0.1, (rSPOTT - 0.38) / (1 - 0.38))))
        rDEFc = max(0, (min(rDMGc + 0.1, (rDEF - 0.10) / (1 - 0.10))))

        wn8 = round((980*rDMGc) + (210*rDMGc*rFRAGc) + (155*rFRAGc *
                                                        rSPOTTc) + (75*rDEFc*rFRAGc) + (145*(min(1.8, rWRc))))

        tank_data.update({'tank_wn8': wn8})
        return tank_data

    def add_career_wn8(self, player_ids: list):
        # Count requests to avoid API spam
        requests_cnt = 0
        for player_id in player_ids:
            # Request and check basic stats
            api_domain, _ = get_wg_api_domain(player_id=player_id)
            # Request detailed stats
            stats_detailed_url = api_domain + \
                self.wg_api_vehicle_statistics + str(player_id)
            stats_detailed_res = requests.get(stats_detailed_url)
            requests_cnt += 1
            stats_detailed_res_raw = rapidjson.loads(stats_detailed_res.text)

            if stats_detailed_res.status_code != 200 or not stats_detailed_res_raw.get('data', {}).get(str(player_id)):
                print(
                    f'Failed to get detailed player stats, WG responded with {stats_detailed_res.status_code}')
            else:
                # Get current detailed stats
                # Sort dict by last played battle
                stats_detailed_tanks = sorted(stats_detailed_res_raw.get(
                    'data').get(str(player_id)), key=lambda x: x['last_battle_time'], reverse=True)
                career_wn8_raw = 0
                career_battles = 0

                for tank_stats in stats_detailed_tanks:
                    tank_id = tank_stats.get('tank_id')
                    tank_stats = tank_stats.get('all')
                    tank_stats.update({'tank_id': tank_id})
                    tank_stats_final = self.add_vehicle_wn8(
                        tank_data=tank_stats)
                    tank_wn8 = tank_stats_final.get('tank_wn8', 0)
                    tank_battles = tank_stats_final.get("battles", 0)
                    career_wn8_raw += (tank_wn8 * tank_battles)
                    career_battles += tank_battles

                career_wn8_weighted = round(career_wn8_raw / career_battles)
                self.players.update_one({'_id': player_id}, {
                                        '$set': {'career_wn8': career_wn8_weighted}})

            if requests_cnt % 100 == 0:
                sleep(5)
