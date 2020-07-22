from rapidjson import dumps


class Rating:
    def __init__(self, replay_data):
        self.replay_data = replay_data
        self.replay_summary = self.replay_data.get('battle_summary')
        self.replay_players = self.replay_data.get('players')

        self.players_lists = [self.replay_summary.get(
            'allies'), self.replay_summary.get('enemies')]

        self.battle_duration = self.replay_summary.get('battle_duration')

        self.eff_multiplyers = {
            'mBRT1_0': {
                'multiplier': 100,
                'string_format': 'RATING',
                'detailed_string_format': '+RATING',
                'lightTank': {
                    'damage_efficiency': 1,
                    'blocked_efficiency': 0,
                    'kill_efficiency': 0.75,
                    'travel_efficiency': 0.75,
                    'shot_efficiency': 0.5,
                    'spotting_efficiency': 1.25,
                    'track_efficiency': 0.75,
                },
                'heavyTank': {
                    'damage_efficiency': 1,
                    'blocked_efficiency': 0.5,
                    'kill_efficiency': 0.5,
                    'travel_efficiency': 0.50,
                    'shot_efficiency': 1,
                    'spotting_efficiency': 0.25,
                    'track_efficiency': 1.25,
                },
                'mediumTank': {
                    'damage_efficiency': 1.25,
                    'blocked_efficiency': 0,
                    'kill_efficiency': 1.25,
                    'travel_efficiency': 0.50,
                    'shot_efficiency': 0.75,
                    'spotting_efficiency': 0.5,
                    'track_efficiency': 0.75,
                },
                'AT-SPG': {
                    'damage_efficiency': 1.5,
                    'blocked_efficiency': 0,
                    'kill_efficiency': 1,
                    'travel_efficiency': 0.25,
                    'shot_efficiency': 1.25,
                    'spotting_efficiency': 0.25,
                    'track_efficiency': 0.75,
                },
            },
            'sBRT1_0': {
                'detailed_string_format': '+RATING',
                'string_format': 'RATING',
                'multiplier': 100,
                'lightTank': {
                    'damage_efficiency': 0.5,
                    'blocked_efficiency': 0,
                    'kill_efficiency': 0.75,
                    'travel_efficiency': 0.75,
                    'shot_efficiency': 0.5,
                    'spotting_efficiency': 1.25,
                    'track_efficiency': 1.25,
                },
                'heavyTank': {
                    'damage_efficiency': 1,
                    'blocked_efficiency': 0.5,
                    'kill_efficiency': 0.5,
                    'travel_efficiency': 0.50,
                    'shot_efficiency': 1,
                    'spotting_efficiency': 0.25,
                    'track_efficiency': 1.25,
                },
                'mediumTank': {
                    'damage_efficiency': 1.25,
                    'blocked_efficiency': 0,
                    'kill_efficiency': 1.25,
                    'travel_efficiency': 0.50,
                    'shot_efficiency': 0.75,
                    'spotting_efficiency': 0.5,
                    'track_efficiency': 0.75,
                },
                'AT-SPG': {
                    'damage_efficiency': 1.5,
                    'blocked_efficiency': 0,
                    'kill_efficiency': 1,
                    'travel_efficiency': 0.25,
                    'shot_efficiency': 1.25,
                    'spotting_efficiency': 0.25,
                    'track_efficiency': 0.75,
                },
            },
            'mBRT1_1': {
                'detailed_string_format': '+RATING',
                'string_format': 'RATING',
                'multiplier': 100,
                'lightTank': {
                    'damage_efficiency': 1.5,
                    'blocked_efficiency': 0.25,
                    'kill_efficiency': 0.75,
                    'travel_efficiency': 1.25,
                    'shot_efficiency': 0.75,
                    'spotting_efficiency': 2.0,
                    'track_efficiency': 0.5,
                },
                'heavyTank': {
                    'damage_efficiency': 1.5,
                    'blocked_efficiency': 1.25,
                    'kill_efficiency': 1.0,
                    'travel_efficiency': 0.75,
                    'shot_efficiency': 1.25,
                    'spotting_efficiency': 0.50,
                    'track_efficiency': 0.75,
                },
                'mediumTank': {
                    'damage_efficiency': 1.75,
                    'blocked_efficiency': 0.75,
                    'kill_efficiency': 1.25,
                    'travel_efficiency': 1.0,
                    'shot_efficiency': 0.75,
                    'spotting_efficiency': 0.75,
                    'track_efficiency': 0.75,
                },
                'AT-SPG': {
                    'damage_efficiency': 2.0,
                    'blocked_efficiency': 0.5,
                    'kill_efficiency': 1.25,
                    'travel_efficiency': 0.50,
                    'shot_efficiency': 1.50,
                    'spotting_efficiency': 0.50,
                    'track_efficiency': 0.75,
                },
            },
            'mBRT1_1A': {
                'detailed_string_format': 'RATING%',
                'string_format': 'RATING%',
                'multiplier': (7/100),
                'lightTank': {
                    'damage_efficiency': 1.5,
                    'blocked_efficiency': 0.25,
                    'kill_efficiency': 0.75,
                    'travel_efficiency': 1.25,
                    'shot_efficiency': 0.75,
                    'spotting_efficiency': 2.0,
                    'track_efficiency': 0.5,
                },
                'heavyTank': {
                    'damage_efficiency': 1.5,
                    'blocked_efficiency': 1.25,
                    'kill_efficiency': 1.0,
                    'travel_efficiency': 0.75,
                    'shot_efficiency': 1.25,
                    'spotting_efficiency': 0.50,
                    'track_efficiency': 0.75,
                },
                'mediumTank': {
                    'damage_efficiency': 1.75,
                    'blocked_efficiency': 0.75,
                    'kill_efficiency': 1.25,
                    'travel_efficiency': 1.0,
                    'shot_efficiency': 0.75,
                    'spotting_efficiency': 0.75,
                    'track_efficiency': 0.75,
                },
                'AT-SPG': {
                    'damage_efficiency': 2.0,
                    'blocked_efficiency': 0.5,
                    'kill_efficiency': 1.25,
                    'travel_efficiency': 0.50,
                    'shot_efficiency': 1.50,
                    'spotting_efficiency': 0.50,
                    'track_efficiency': 0.75,
                },
            }
        }

        self.total_dmg = [0, 0]      # Total by team
        self.total_shots = [0, 0]    # Total by team
        self.damage_recieved = [0, 0]
        self.tatal_shots_made = [0, 0]

        self.players_count = round(len(self.replay_data.get('players')))
        self.lighttank_count = [0, 0]
        self.mediumtank_count = [0, 0]

        self.average_vehicle_alpha_efficiency = 0
        self.average_distance_travelled = 0

        for player in self.replay_data.get('players'):
            player_data = self.replay_data.get('players').get(player)

            player_team = player_data.get('team') - 1

            self.total_dmg[player_team] += player_data.get(
                'performance').get('damage_made')

            self.damage_recieved[player_team] += player_data.get(
                'performance').get('damage_received')
            self.total_shots[player_team] += player_data.get(
                'performance').get('shots_pen')
            self.tatal_shots_made[player_team] += player_data.get(
                'performance').get('shots_made')

            self.average_vehicle_alpha_efficiency += player_data.get(
                'vehicle_alpha_efficiency')
            self.average_distance_travelled += player_data.get(
                'performance').get('distance_travelled')

            if player_data.get('player_vehicle_type') == 'lightTank':
                self.lighttank_count[player_team] += 1

            if player_data.get('player_vehicle_type') == 'mediumTank':
                self.mediumtank_count[player_team] += 1

        self.average_vehicle_alpha_efficiency = self.average_vehicle_alpha_efficiency / \
            self.players_count
        self.average_distance_travelled = self.average_distance_travelled / self.players_count
        self.avg_damage_recieved = [(self.damage_recieved[0] / len(
            self.players_lists[0])), (self.damage_recieved[1] / len(self.players_lists[0]))]

        self.avg_shots_made = [
            (self.tatal_shots_made[0] / len(self.players_lists[0])), (self.tatal_shots_made[1] / len(self.players_lists[1]))]

        self.tank_hp_avg = [(self.total_dmg[0] /
                             len(self.players_lists[0])), (self.total_dmg[1] / len(self.players_lists[1]))]

        self.shots_avg_dmg = [(self.total_dmg[0] /
                               self.total_shots[0]), (self.total_dmg[1] / self.total_shots[1])]

        self.avg_damage = (
            self.total_dmg[0] + self.total_dmg[1]) / self.players_count

    def get_brt(self, rating_version='mBRT1_1'):
        best_rating = {}
        rating_descr = {}

        for player in self.replay_data.get('players'):
            player_rating = {}

            player_data = self.replay_data.get('players').get(player)
            player_name = player_data.get('nickname')
            player_team_id = player_data.get('team') - 1
            player_wr = player_data.get('player_wr')

            survived_bool = True
            if player_data.get('performance').get('hitpoints_left') == 0:
                survived_bool = False

            tank_hp_avg = (self.tank_hp_avg[1] + self.tank_hp_avg[0]) / 2
            shots_avg_damage = self.shots_avg_dmg[player_team_id]
            travel_avg = self.average_distance_travelled

            shots_fired = player_data.get('performance').get('shots_made')
            if shots_fired == 0:
                shots_fired = 1

            shots_penetrated = player_data.get(
                'performance').get('shots_pen')

            time_alive = player_data.get('performance').get('time_alive')
            player_rating['time_alive'] = time_alive

            damage_blocked = player_data.get(
                'performance').get('damage_blocked') or shots_avg_damage * player_data.get(
                'performance').get('hits_bounced')
            player_rating['damage_blocked'] = damage_blocked

            distance_travelled = player_data.get(
                'performance').get('distance_travelled')
            player_rating['distance_travelled'] = distance_travelled

            damage_assisted = player_data.get(
                'performance').get('damage_assisted')
            player_rating['damage_assisted'] = damage_assisted

            damage_assisted_track = player_data.get(
                'performance').get('damage_assisted_track')
            player_rating['damage_assisted_track'] = damage_assisted_track

            enemies_spotted = player_data.get(
                'performance').get('enemies_spotted')
            player_rating['enemies_spotted'] = enemies_spotted

            damage_made = player_data.get(
                'performance').get('damage_made')
            player_rating['damage_made'] = damage_made

            kills = player_data.get(
                'performance').get('enemies_destroyed')
            player_rating['kills'] = kills

            tank_type = player_data.get('player_vehicle_type')
            tank_name = player_data.get('player_vehicle')
            # Not used, unable to pull vehicle chars without spamming requests to WG API
            tank_hp = 2000
            travel_avg = 1000  # How long a tank should travel on average

            hp_left = player_data.get('performance').get('hitpoints_left')

            enemies = self.players_lists[0]
            if player_team_id == 0:
                enemies = self.players_lists[1]

            lighttank_count = self.lighttank_count[player_team_id]
            if lighttank_count == 0:
                lighttank_count = self.mediumtank_count[player_team_id]

            damage_rating = round((((damage_made) / tank_hp_avg) *
                                   self.eff_multiplyers.get(rating_version).get(
                tank_type).get('damage_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['damage_rating'] = damage_rating

            kill_rating = round(((kills / (len(enemies))) *
                                 self.eff_multiplyers.get(rating_version).get(
                tank_type).get('kill_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['kill_rating'] = kill_rating

            travel_rating = round(((distance_travelled / travel_avg) *
                                   self.eff_multiplyers.get(rating_version).get(
                tank_type).get('travel_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['travel_rating'] = travel_rating

            shot_rating = round((((shots_penetrated) /
                                  (shots_fired)) *
                                 self.eff_multiplyers.get(rating_version).get(
                tank_type).get('shot_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['shot_rating'] = shot_rating

            spotting_rating = round((((enemies_spotted) / (len(enemies)) * (lighttank_count / 2)) *
                                     self.eff_multiplyers.get(rating_version).get(
                tank_type).get('spotting_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['spotting_rating'] = spotting_rating

            blocked_rating = round(((damage_blocked / tank_hp_avg) *
                                    self.eff_multiplyers.get(rating_version).get(
                tank_type).get('blocked_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['blocked_rating'] = blocked_rating

            track_rating = round((((damage_assisted_track + damage_assisted) / tank_hp_avg) *
                                  self.eff_multiplyers.get(rating_version).get(
                tank_type).get('track_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['track_rating'] = track_rating

            rating = round(((damage_rating + kill_rating +
                             travel_rating + shot_rating + spotting_rating + track_rating + blocked_rating)))
            player_rating['rating'] = rating

            for rating_name in player_rating:
                rating_value = player_rating.get(rating_name)

                player_data[f'{rating_name}_value'] = rating_value

                player_data[rating_name] = self.eff_multiplyers.get(
                    rating_version).get('string_format').replace('RATING', str(rating_value))

                if best_rating.get(rating_name, 0) < rating_value:
                    best_rating[rating_name] = rating_value

        rating_descr['rating_descr'] = 'Total Rating'
        rating_descr['blocked_rating_descr'] = 'Damage Blocked'
        rating_descr['track_rating_descr'] = 'Damage from Spotting'
        rating_descr['spotting_rating_descr'] = 'Spotting'
        rating_descr['shot_rating_descr'] = 'Accuracy'
        rating_descr['travel_rating_descr'] = 'Movement'
        rating_descr['kill_rating_descr'] = 'Kills'
        rating_descr['damage_rating_descr'] = 'Damage'
        rating_descr['kills_descr'] = 'Kills'
        rating_descr['damage_made_descr'] = 'Damage Made'
        rating_descr['player_wr_descr'] = 'Winrate'
        rating_descr['time_alive_descr'] = 'Time Alive'
        rating_descr['damage_blocked_descr'] = 'Damage Blocked'
        rating_descr['distance_travelled_descr'] = 'Distance Travelled'
        rating_descr['damage_assisted_descr'] = 'Damage from Spotting'
        rating_descr['damage_assisted_track_descr'] = 'Damage from Tracking'
        rating_descr['enemies_spotted_descr'] = 'Vehicles Spotted'

        self.replay_data['best_rating'] = best_rating
        self.replay_data['rating_descr'] = rating_descr
        # print(dumps(self.replay_data, indent=2))

        return self.replay_data
