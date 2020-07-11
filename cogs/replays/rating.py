class Rating:
    def __init__(self, replay_data):
        self.replay_data = replay_data
        self.replay_summary = self.replay_data.get('summary')
        self.replay_players = self.replay_data.get('players')

        self.eff_multiplyers = {
            'mBRT1_0': {
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
            }
        }

    def calculate_rating(self, rating_version):
        total_dmg = 0
        total_shots = 0
        players_count = round(len(self.replay_data.get('players')))
        for player in self.replay_data.get('players'):
            player_data = self.replay_data.get('players').get(player)
            total_dmg += player_data.get('performance').get('damage_made')
            total_shots += player_data.get('performance').get('shots_pen')

        tank_hp_avg = total_dmg / players_count
        shots_avg_dmg = total_dmg / total_shots

        for player in self.replay_data.get('players'):
            player_data = self.replay_data.get('players').get(player)
            player_name = player_data.get('nickname')

            survived_bool = True
            if player_data.get('performance').get('hitpoints_left') == 0:
                survived_bool = False

            shots_fired = player_data.get('performance').get('shots_made')
            if shots_fired == 0:
                shots_fired = 1
            shots_penetrated = player_data.get('performance').get('shots_pen')
            enemies_destroyed = player_data.get(
                'performance').get('enemies_destroyed')
            time_alive = player_data.get('performance').get('time_alive')
            damage_blocked = player_data.get(
                'performance').get('damage_blocked') or shots_avg_dmg * player_data.get(
                'performance').get('hits_bounced')
            distance_travelled = player_data.get(
                'performance').get('distance_travelled')
            damage_assisted = player_data.get(
                'performance').get('damage_assisted')
            damage_assisted_track = player_data.get(
                'performance').get('damage_assisted_track')
            enemies_spotted = player_data.get(
                'performance').get('enemies_spotted')
            damage_made = player_data.get('performance').get('damage_made')
            kills = player_data.get('performance').get('enemies_destroyed')

            tank_type = player_data.get('vehicle').get('type')
            tank_name = player_data.get('vehicle').get('name')
            tank_hp = 2000  # Not used, unable to pull vehicle chars without spamming requests to WG API
            travel_avg = 1000  # How long a tank should travel on average

            platoon_number = player_data.get('performance').get('squad_index')

            hp_left = player_data.get('performance').get('hitpoints_left')
            survived_bool = True
            if hp_left < 1:
                survived_bool = False

            damage_efficiency = ((damage_made + damage_assisted) / tank_hp_avg) * \
                self.eff_multiplyers.get(rating_version).get(
                    tank_type).get('damage_efficiency')

            kill_efficiency = (kills / 7) * \
                self.eff_multiplyers.get(rating_version).get(
                    tank_type).get('kill_efficiency')

            travel_efficiency = (distance_travelled / travel_avg) * \
                self.eff_multiplyers.get(rating_version).get(
                    tank_type).get('travel_efficiency')

            shot_efficiency = ((shots_penetrated) /
                               (shots_fired)) * \
                self.eff_multiplyers.get(rating_version).get(
                    tank_type).get('shot_efficiency')

            spotting_efficiency = ((enemies_spotted) / (players_count / 2)) * \
                self.eff_multiplyers.get(rating_version).get(
                    tank_type).get('spotting_efficiency')

            blocked_efficiency = (damage_blocked / tank_hp_avg) * \
                self.eff_multiplyers.get(rating_version).get(
                    tank_type).get('blocked_efficiency')

            track_efficiency = (damage_assisted_track / tank_hp_avg) * \
                self.eff_multiplyers.get(rating_version).get(
                    tank_type).get('track_efficiency')

            rating = round(((damage_efficiency + kill_efficiency +
                             travel_efficiency + shot_efficiency + spotting_efficiency + track_efficiency + blocked_efficiency) * 100))

            # print(
            #     f'[{player_id}] {tank_name}, DMG:{damage_efficiency}({damage_made})[{damage_blocked}], KILLS:{kill_efficiency}({kills}), DIST:{travel_efficiency}({distance_travelled}), SHOTS: {shot_efficiency}({shots_fired}), SPOT: {spotting_efficiency}({enemies_spotted}), TRACK: {track_efficiency}, vRT: {rating}')

            player_data['rating'] = rating

        return self.replay_data
