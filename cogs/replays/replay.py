import requests
import rapidjson


class Replay:
    def __init__(self, replay_urls):
        self.wg_app_token = 'add73e99679dd4b7d1ed7218fe0be448'
        self.wg_api_url_end = f'/wotb/account/info/?&application_id={self.wg_app_token}&account_id='
        self.wg_tanks_api_url_end = f'/wotb/encyclopedia/vehicles/?&application_id={self.wg_app_token}&fields=tier,is_premium,type,name,nation,default_profile&tank_id='
        self.wg_tank_stats_api_url_end = f'/wotb/tanks/stats/?&application_id={self.wg_app_token}&fields=all&account_id='

        self.proxy_url = "https://am-wg-proxy-eu.herokuapp.com/get"

        self.base_view_url = 'https://replays.wotinspector.com/en/view/'
        self.base_api_url = 'https://wotinspector.com/api/replay/upload/?details=full&private=1&title=Aftermath&url='

        self.replay_urls = replay_urls
        self.api_urls = []

        for url in replay_urls:
            self.api_urls.append(self.base_api_url + url)

        self.replays = {}

        self.room_type_key = {
            0: 'Unknown',
            1: 'Regular Battle',
            2: 'Training Room',
            4: 'Tournament Battle',
            5: 'Tournament Battle',
            7: 'Rating Battle',
            8: 'Mad Games',
            22: 'Realistic Battle',
            23: 'Uprising',
            24: 'Gravity Force',
        }
        # Will default to extended results screen
        self.special_room_types = [2, 4, 5]

    def process_replays(self):
        for url in self.api_urls:
            res = requests.get(url)

            if not res:
                raise Exception('Unable to reach WoTInspector. Please try again later.')

            replay_data = rapidjson.loads(res.text)

            if not replay_data:
                raise Exception('Unable to reach WoTInspector API')

            replay_id = replay_data.get('data').get(
                'view_url').replace(self.base_view_url, '')

            battle_summary = self.gather_battle_summary(replay_data)

            protagonist_id = replay_data.get(
                'data').get('summary').get('protagonist')
            players = self.gather_players(
                replay_data.get('data').get('summary'))

            download_url = replay_data.get('data').get('download_url')

            replay = {
                'download_url': download_url,
                'battle_summary': battle_summary,
                'players': players
            }
            self.replays[replay_id] = replay

        return self.replays

    def gather_battle_summary(self, data):

        replay_data = data.get('data')
        winner_team = replay_data.get('summary').get('winner_team')
        battle_type = replay_data.get('summary').get('battle_type')
        self.battle_duration = replay_data.get(
            'summary').get('battle_duration')
        battle_result = replay_data.get('summary').get('battle_result')
        battle_start_time = replay_data.get(
            'summary').get('battle_start_time')
        map_name = replay_data.get('summary').get('map_name')
        room_type = replay_data.get('summary').get('room_type')
        room_type_str = self.room_type_key.get(
            int(room_type), 'Missing, please report')
        protagonist = replay_data.get('summary').get('protagonist')
        exp_total = replay_data.get('summary').get('exp_total')
        credits_total = replay_data.get('summary').get('credits_total')
        mastery_badge = replay_data.get('summary').get('mastery_badge')

        allies = replay_data.get('summary').get('allies')
        enemies = replay_data.get('summary').get('enemies')

        battle_type_str = ''
        if battle_type == 0:
            battle_type_str = '(Encounter)'
        if battle_type == 1:
            battle_type_str = '(Supremacy)'

        battle_summary = {
            "protagonist": protagonist,
            "enemies": enemies,
            "allies": allies,
            "winner_team": winner_team,
            "battle_result": battle_result,
            "battle_duration": self.battle_duration,
            "battle_start_timestamp": battle_start_time,
            "exp_total": exp_total,
            "mastery_badge": mastery_badge,
            "credits_total": credits_total,
            "map_name": map_name,
            "room_type": room_type,
            "room_type_str": room_type_str,
            "special_room_types": self.special_room_types,
            "battle_type": battle_type,
            "battle_type_str": battle_type_str,
        }

        return battle_summary

    def gather_players(self, replay_summary):
        players = {}
        protagonist_id = replay_summary.get('protagonist')
        players_all = replay_summary.get('details')

        enemies = replay_summary.get('enemies')
        allies = replay_summary.get('allies')

        # Get stats for each player from WG API
        player_ids_all = replay_summary.get(
            'allies') + replay_summary.get('enemies')
        player_ids_all_str = ','.join((str(player)
                                       for player in player_ids_all))
        wg_api_domain, _ = self.get_wg_api_domain(protagonist_id)

        res = requests.get(wg_api_domain + self.wg_api_url_end + player_ids_all_str)

        if not res:
            raise Exception('Unable to reach Wargaming servers. Please try again later.')

        players_stats = rapidjson.loads(res.text).get('data')

        if not players_stats:
            raise Exception('Unable to reach WG API (Fetching player data)')

        # Get all vehicle data from WG API
        vehicles_all = []
        for player in players_all:
            vehicle = player.get('vehicle_descr')
            if vehicle not in vehicles_all:
                vehicles_all.append(vehicle)
        vehicles_all_str = ','.join((str(vehicle)
                                     for vehicle in vehicles_all))

        res = requests.get(
            wg_api_domain + self.wg_tanks_api_url_end + vehicles_all_str)

        if not res:
            raise Exception('Unable to reach Wargaming servers. Please try again later.')

        vehicles_all_data = rapidjson.loads(res.text).get('data')

        if not vehicles_all_data:
            raise Exception('Unable to reach WG API (Fetching vehicle data)')

        for player in players_all:
            player_id = str(player.get('dbid'))

            if int(player_id) in enemies:
                team = 2
            else:
                team = 1

            clan_tag = player.get('clan_tag')
            nickname = players_stats.get(player_id).get('nickname')
            stats = players_stats.get(player_id).get('statistics').get('all')

            vehicle = vehicles_all_data.get(str(
                player.get('vehicle_descr')), {}) or {}

            time_alive = player.get('time_alive') or 1

            shots_made = player.get('shots_made') or 1
            if shots_made == 0:
                shots_made = 1

            damage_made = player.get('damage_made') or 0
            vehicle_alpha_efficiency = damage_made * \
                (time_alive / self.battle_duration)

            vehicle_id = player.get('vehicle_descr')

            try:
                res = requests.get(
                    wg_api_domain + self.wg_tank_stats_api_url_end + player_id + f'&tank_id={vehicle_id}')

                if not res:
                    raise Exception('Unable to reach Wargaming servers. Please try again later.')

                vehicle_stats = rapidjson.loads(res.text).get('data').get(player_id)[0].get('all')
            except:
                vehicle_stats = None

            player_wins = stats.get('wins')
            player_battles = stats.get('battles')
            if player_battles == 0:
                player_battles = 1
            player_vehicle = vehicle.get('name', 'Unknown')
            player_vehicle_type = vehicle.get('type', 'unknown')
            player_vehicle_tier = vehicle.get('tier', 0)
            hp_left = player.get('hitpoints_left') or 0
            survived = True
            if hp_left <= 0:
                survived = False

            try:
                vehicle_wins = stats.get('wins')
                vehicle_battles = stats.get('battles')
                vehicle_wr = "%.2f" % round(
                    (vehicle_wins / vehicle_battles * 100), 2) + '%'
            except:
                vehicle_wins = 0
                vehicle_battles = 0
                vehicle_wr = '0%'

            player_wr = "%.2f" % round(
                (player_wins / player_battles * 100), 2) + '%'

            platoon_number = player.get('squad_index')
            platoon_str = ''
            if platoon_number:
                platoon_str = f'{platoon_number}'

            kills = player.get('enemies_destroyed') or 0
            hero_bonus_exp = player.get('hero_bonus_exp') or 0

            player_data = {
                player_id: {
                    'nickname': nickname,
                    'clan_tag': clan_tag,
                    'team': team,
                    'vehicle': vehicle,
                    'vehicle_stats': vehicle_stats,
                    'vehicle_alpha_efficiency': vehicle_alpha_efficiency,
                    'performance': player,
                    'stats': stats,
                    'damage': damage_made,
                    'kills': kills,
                    'survived': survived,
                    'hero_bonus_exp': hero_bonus_exp,
                    'platoon_str': platoon_str,
                    'player_vehicle': player_vehicle,
                    'player_vehicle_type': player_vehicle_type,
                    'player_vehicle_tier': player_vehicle_tier,
                    'vehicle_battles': vehicle_battles,
                    'vehicle_wr': vehicle_wr,
                    'player_wr': player_wr,
                }
            }

            players.update(player_data)
        return players

    def get_wg_api_domain(self, player_id):
        # Detect realm
        length = len(str(player_id))
        if length == 8:
            player_realm = 'ru'
            api_domain = 'http://api.wotblitz.ru'

        elif length == 9:
            player_realm = 'eu'
            api_domain = 'http://api.wotblitz.eu'

        elif length == 10:
            player_realm = 'na'
            api_domain = 'http://api.wotblitz.com'

        else:
            player_realm = 'asia'
            api_domain = 'http://api.wotblitz.asia'

        return api_domain, player_realm
