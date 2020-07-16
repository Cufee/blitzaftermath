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

        for player in self.replay_data.get('players'):
            player_data = self.replay_data.get('players').get(player)
            player_name = player_data.get('nickname')
            player_team_id = player_data.get('team') - 1

            survived_bool = True
            if player_data.get('performance').get('hitpoints_left') == 0:
                survived_bool = False

            tank_hp_avg = self.tank_hp_avg[player_team_id]
            shots_avg_damage = self.shots_avg_dmg[player_team_id]
            travel_avg = self.average_distance_travelled

            shots_fired = player_data.get('performance').get('shots_made')
            if shots_fired == 0:
                shots_fired = 1
            shots_penetrated = player_data.get(
                'performance').get('shots_pen')
            enemies_destroyed = player_data.get(
                'performance').get('enemies_destroyed')
            time_alive = player_data.get('performance').get('time_alive')
            damage_blocked = player_data.get(
                'performance').get('damage_blocked') or shots_avg_damage * player_data.get(
                'performance').get('hits_bounced')
            distance_travelled = player_data.get(
                'performance').get('distance_travelled')
            damage_assisted = player_data.get(
                'performance').get('damage_assisted')
            damage_assisted_track = player_data.get(
                'performance').get('damage_assisted_track')
            enemies_spotted = player_data.get(
                'performance').get('enemies_spotted')
            damage_made = player_data.get(
                'performance').get('damage_made')
            kills = player_data.get(
                'performance').get('enemies_destroyed')

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

            damage_efficiency = round((((damage_made + damage_assisted) / tank_hp_avg) *
                                       self.eff_multiplyers.get(rating_version).get(
                tank_type).get('damage_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))

            kill_efficiency = round(((kills / (len(enemies))) *
                                     self.eff_multiplyers.get(rating_version).get(
                tank_type).get('kill_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))

            travel_efficiency = round(((distance_travelled / travel_avg) *
                                       self.eff_multiplyers.get(rating_version).get(
                tank_type).get('travel_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))

            shot_efficiency = round((((shots_penetrated) /
                                      (shots_fired)) *
                                     self.eff_multiplyers.get(rating_version).get(
                tank_type).get('shot_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))

            spotting_efficiency = round((((enemies_spotted) / (len(enemies)) * lighttank_count) *
                                         self.eff_multiplyers.get(rating_version).get(
                tank_type).get('spotting_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))

            blocked_efficiency = round(((damage_blocked / tank_hp_avg) *
                                        self.eff_multiplyers.get(rating_version).get(
                tank_type).get('blocked_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))

            track_efficiency = round(((damage_assisted_track / tank_hp_avg) *
                                      self.eff_multiplyers.get(rating_version).get(
                tank_type).get('track_efficiency') * (self.eff_multiplyers.get(rating_version).get('multiplier'))))

            rating = round(((damage_efficiency + kill_efficiency +
                             travel_efficiency + shot_efficiency + spotting_efficiency + track_efficiency + blocked_efficiency)))

            player_data['rating_value'] = rating
            player_data['rating'] = self.eff_multiplyers.get(
                rating_version).get('string_format').replace('RATING', str(rating))
            player_data['damage_rating'] = self.eff_multiplyers.get(
                rating_version).get('detailed_string_format').replace('RATING', str(damage_efficiency))
            player_data['kill_rating'] = self.eff_multiplyers.get(
                rating_version).get('detailed_string_format').replace('RATING', str(kill_efficiency))
            player_data['shot_rating'] = self.eff_multiplyers.get(
                rating_version).get('detailed_string_format').replace('RATING', str(shot_efficiency))
            player_data['spotting_rating'] = self.eff_multiplyers.get(
                rating_version).get('detailed_string_format').replace('RATING', str(spotting_efficiency))
            player_data['track_rating'] = self.eff_multiplyers.get(
                rating_version).get('detailed_string_format').replace('RATING', str(track_efficiency))
            player_data['blocked_rating'] = self.eff_multiplyers.get(
                rating_version).get('detailed_string_format').replace('RATING', str(blocked_efficiency))

            # print(
            #     f'{player_name}[DMG:{(damage_made + damage_assisted)}][BLK:{round((damage_blocked / tank_hp_avg), 2)}][SHT:{round(((shots_penetrated) / (shots_fired)), 2)}]')

            # print(f'[{player_name}] {tank_name}, DMG:{damage_efficiency}({damage_made})[{damage_blocked}], KILLS:{kill_efficiency}({kills}), DIST:{travel_efficiency}({distance_travelled}), SHOTS: {shot_efficiency}({shots_fired}), SPOT: {spotting_efficiency}({enemies_spotted}), TRACK: {track_efficiency}, vRT: {rating}')

        return self.replay_data

    def get_vbr(self, version='1_0'):

        for player in self.replay_data.get('players'):
            player_data = self.replay_data.get('players').get(player)
            player_name = player_data.get('nickname')

            player_team_id = player_data.get('team') - 1

            shots_fired = player_data.get('performance').get('shots_made')
            if shots_fired == 0:
                shots_fired = 1

            shots_hit = player_data.get(
                'performance').get('shots_hit')
            shots_penetrated = player_data.get(
                'performance').get('shots_pen')
            enemies_destroyed = player_data.get(
                'performance').get('enemies_destroyed')

            vehicle_alpha_efficiency = player_data.get(
                'vehicle_alpha_efficiency')

            time_alive = player_data.get('performance').get('time_alive')

            shots_avg_damage = self.shots_avg_dmg[player_team_id]

            damage_blocked = player_data.get(
                'performance').get('damage_blocked') or shots_avg_damage * player_data.get(
                'performance').get('hits_bounced')

            damage_received = player_data.get(
                'performance').get('damage_received')

            distance_travelled = player_data.get(
                'performance').get('distance_travelled')

            damage_assisted = player_data.get(
                'performance').get('damage_assisted')

            damage_assisted_track = player_data.get(
                'performance').get('damage_assisted_track')

            enemies_spotted = player_data.get(
                'performance').get('enemies_spotted')

            damage_made = player_data.get(
                'performance').get('damage_made')

            kills = player_data.get(
                'performance').get('enemies_destroyed')

            lighttank_count = self.lighttank_count[player_team_id]
            if lighttank_count == 0:
                lighttank_count = self.mediumtank_count[player_team_id]

            tank_type = player_data.get('player_vehicle_type')
            # Not used, unable to pull vehicle chars without spamming requests to WG API
            tank_hp = 2000
            travel_avg = 1000  # How long a tank should travel on average

            enemies = self.players_lists[0]
            if player_team_id == 0:
                enemies = self.players_lists[1]

            enemie_team = 0
            if player_team_id == 0:
                enemie_team = 1

            damage_efficiency = round((damage_made / (self.avg_damage)), 2)

            shot_efficiency = shots_penetrated / shots_fired

            # Not working as expected, need to counter platyers who made 1 shot
            alpha_efficiency = (vehicle_alpha_efficiency)

            kill_bonus = round(
                (kills / (self.battle_duration / 60)), 2)

            engagement_rating = round(((shot_efficiency) * (
                (distance_travelled) / self.average_distance_travelled) * (damage_efficiency) + kill_bonus), 2)

            spotting_rating = round((enemies_spotted *
                                     lighttank_count / len(enemies)), 2)

            survival_rating = round((((time_alive * 10) +
                                      damage_blocked) / (self.battle_duration * 10)), 2)

            assistance_rating = round(((
                damage_assisted + damage_assisted_track) / (self.avg_damage_recieved[enemie_team])), 2)

            rating = round((engagement_rating + spotting_rating +
                            survival_rating + assistance_rating) * 100)

            player_data['rating'] = rating
            player_data['rating_value'] = rating
            player_data['kill_rating'] = f'+{round(kill_bonus * 100)}'
            player_data['engagement_rating'] = f'+{round(engagement_rating * 100)}'
            player_data['spotting_rating'] = f'+{round(spotting_rating * 100)}'
            player_data['survival_rating'] = f'+{round(survival_rating * 100)}'
            player_data['assistance_rating'] = f'+{round(assistance_rating * 100)}'

            print(
                f'[{player_name}] -> ENGR:{engagement_rating} / SHT:{shot_efficiency} / DMGE:{damage_efficiency} / TRVL:{(distance_travelled) / self.average_distance_travelled} / KB:{kill_bonus}')

            # print(
            #     f'[{player_name}] R:{rating} ER:{round((engagement_rating), 2)} DE:[{damage_efficiency}](AE:{round((vehicle_alpha_efficiency), 2)}([{shot_efficiency}]{shots_fired}/{shots_penetrated}), aAE:{round((self.average_vehicle_alpha_efficiency), 2)}, ED:{expected_damage}) SR:{spotting_rating} SPR:{spotting_rating} SRVR:{survival_rating}(TA:{time_alive}, DR:{damage_received}, DB:{damage_blocked}) AR:{assistance_rating}')

        return self.replay_data
