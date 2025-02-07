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
                'unknown': {
                    'damage_efficiency': 0,
                    'blocked_efficiency': 0,
                    'kill_efficiency': 0,
                    'travel_efficiency': 0,
                    'shot_efficiency': 0,
                    'spotting_efficiency': 0,
                    'track_efficiency': 0,
                },
                'lightTank': {
                    'damage_efficiency': 1.5,
                    'blocked_efficiency': 0.25,
                    'kill_efficiency': 1.0,
                    'travel_efficiency': 0.75,
                    'shot_efficiency': 0.75,
                    'spotting_efficiency': 2.0,
                    'track_efficiency': 0.75,
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
        self.team_points_total = [300, 300]

        for player in self.replay_data.get('players'):
            player_data = self.replay_data.get('players').get(player)

            player_team = player_data.get('team') - 1
            if player_team == 0:
                enemy_team = 1
            else:
                enemy_team = 0

            self.team_points_total[player_team] += player_data.get(
                'performance').get('wp_points_earned') or 0
            self.team_points_total[enemy_team] -= player_data.get(
                'performance').get('wp_points_stolen') or 0

            self.total_dmg[player_team] += player_data.get(
                'performance').get('damage_made') or 0

            self.damage_recieved[player_team] += player_data.get(
                'performance').get('damage_received') or 0
            self.total_shots[player_team] += player_data.get(
                'performance').get('shots_pen') or 0
            self.tatal_shots_made[player_team] += player_data.get(
                'performance').get('shots_made') or 0

            self.average_vehicle_alpha_efficiency += player_data.get(
                'vehicle_alpha_efficiency') or 0
            self.average_distance_travelled += player_data.get(
                'performance').get('distance_travelled') or 0

            if player_data.get('player_vehicle_type') == 'lightTank':
                self.lighttank_count[player_team] += 1

            if player_data.get('player_vehicle_type') == 'mediumTank':
                self.mediumtank_count[player_team] += 1

        # Handle future 0 Division errors
        if len(self.players_lists[1]) == 0:
            self.players_lists = [
                [self.players_lists[0]], ['NA']]

        if self.total_shots[0] == 0 or self.total_shots[1] == 0:
            self.total_shots = [1, 1]

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

        self.team_points = {
            0: self.team_points_total[0],
            1: self.team_points_total[1],
        }

    def get_brt(self, rating_version='mBRT1_1'):
        best_rating = {}
        rating_descr = {}

        for player in self.replay_data.get('players'):
            player_rating = {}

            player_data = self.replay_data.get('players').get(player)
            player_name = player_data.get('nickname')
            player_team_id = player_data.get('team') - 1
            player_wr = player_data.get('player_wr')

            performance = player_data.get(
                'performance') or None
            if not performance:
                raise Exception(
                    'Player performance not avaialable or None. Unable to calculate rating')

            survived_bool = True
            if player_data.get('performance').get('hitpoints_left') == 0:
                survived_bool = False

            tank_hp_avg = (self.tank_hp_avg[1] + self.tank_hp_avg[0]) / 2
            if tank_hp_avg == 0:
                tank_hp_avg = 1
            shots_avg_damage = self.shots_avg_dmg[player_team_id] or 1
            travel_avg = self.average_distance_travelled or 500
            if travel_avg == 0:
                travel_avg == 500
            shots_fired = player_data.get('performance').get('shots_made') or 1
            if shots_fired == 0:
                shots_fired = 1

            shots_penetrated = player_data.get(
                'performance').get('shots_pen') or 0

            player_rating['accuracy'] = f'{round(((shots_penetrated / shots_fired) * 100))}%'
            player_rating['accuracy_value'] = round(
                ((shots_penetrated / shots_fired) * 100))

            player_rating['wp_points_earned'] = player_data.get(
                'performance').get('wp_points_earned') or 0
            player_rating['wp_points_stolen'] = player_data.get(
                'performance').get('wp_points_stolen') or 0

            time_alive = player_data.get('performance').get('time_alive') or 0
            player_rating['time_alive'] = round((time_alive / 60), 1)

            hits_bounced = performance.get('hits_bounced') or 0

            damage_blocked = performance.get(
                'damage_blocked') or shots_avg_damage * hits_bounced
            player_rating['damage_blocked'] = round(damage_blocked)

            distance_travelled = player_data.get(
                'performance').get('distance_travelled') or 0
            player_rating['distance_travelled'] = round(distance_travelled)

            damage_assisted_track = player_data.get(
                'performance').get('damage_assisted_track') or 0

            damage_assisted = player_data.get(
                'performance').get('damage_assisted') or 0

            damage_assisted_total = round(
                damage_assisted + damage_assisted_track)
            player_rating['damage_assisted'] = damage_assisted_total

            enemies_spotted = player_data.get(
                'performance').get('enemies_spotted') or 0
            player_rating['enemies_spotted'] = round(enemies_spotted)

            damage_made = player_data.get(
                'performance').get('damage_made') or 0

            player_rating['damage_made'] = round(damage_made)

            kills = player_data.get(
                'performance').get('enemies_destroyed') or 0
            player_rating['kills'] = round(kills)

            tank_type = player_data.get('player_vehicle_type', 'mediumTank')
            tank_name = player_data.get('player_vehicle', 'Unknown')
            # Not used, unable to pull vehicle chars without spamming requests to WG API
            tank_hp = 2000

            damage_recieved = player_data.get(
                'performance').get('damage_received') or 1
            hp_left = player_data.get('performance').get('hitpoints_left') or 1
            total_hp = hp_left + damage_recieved

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

            travel_rating = round(((distance_travelled / (travel_avg * 1.5)) *
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

            assist_rating = round((((damage_assisted_total) / tank_hp_avg) *
                                   self.eff_multiplyers.get(rating_version).get(
                tank_type).get('track_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))
            player_rating['assist_rating'] = assist_rating

            rating = round(((damage_rating + kill_rating +
                             travel_rating + shot_rating + spotting_rating + assist_rating + blocked_rating)))
            player_rating['rating'] = rating

            for rating_name in player_rating:
                rating_value = player_rating.get(rating_name)
                player_data[f'{rating_name}_value'] = rating_value

                player_data[rating_name] = self.eff_multiplyers.get(
                    rating_version).get('string_format').replace('RATING', str(rating_value))
                try:
                    if best_rating.get(rating_name, 0) < rating_value:
                        best_rating[rating_name] = rating_value
                except:
                    if best_rating.get(rating_name, 0) < player_rating.get(f'{rating_name}_value'):
                        best_rating[rating_name] = rating_value

        rating_descr['rating_descr'] = 'Aftermath Rating'
        rating_descr['blocked_rating_descr'] = 'Damage Blocked'
        rating_descr['assist_rating_descr'] = 'Assited Damage'
        rating_descr['spotting_rating_descr'] = 'Spotting'
        rating_descr['shot_rating_descr'] = 'Accuracy'
        rating_descr['accuracy_descr'] = 'Accuracy %'
        rating_descr['travel_rating_descr'] = 'Movement'
        rating_descr['kill_rating_descr'] = 'Kills'
        rating_descr['damage_rating_descr'] = 'Damage'
        rating_descr['kills_descr'] = 'Kills'
        rating_descr['damage_made_descr'] = 'Damage Done'
        rating_descr['player_wr_descr'] = 'Winrate'
        rating_descr['time_alive_descr'] = 'Time Alive (min)'
        rating_descr['damage_blocked_descr'] = 'Damage Blocked'
        rating_descr['distance_travelled_descr'] = 'Distance Traveled (m)'
        rating_descr['damage_assisted_descr'] = 'Assited Damage'
        rating_descr['enemies_spotted_descr'] = 'Vehicles Spotted'
        rating_descr['wp_points_earned_descr'] = 'Points Earned'
        rating_descr['wp_points_stolen_descr'] = 'Points Denied'

        self.replay_data['best_rating'] = best_rating
        self.replay_data['team_points'] = self.team_points
        self.replay_data['rating_descr'] = rating_descr
        # print(dumps(self.replay_data, indent=2))

        return self.replay_data
