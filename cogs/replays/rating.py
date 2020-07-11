class Rating:
    def __init__(self, replay_data):
        self.replay_data = replay_data
        self.replay_summary = self.replay_data.get('summary')
        self.replay_players = self.replay_data.get('players')

    def calculate_rating(self):
        for player in self.replay_data.get('players'):
            player_data = self.replay_data.get('players').get(player)
            player_name = player_data.get('nickname')

            survived_bool = True
            if player_data.get('performance').get('hitpoints_left') == 0:
                survived_bool = False

            shots_fired = player_data.get('performance').get('shots_made')
            shots_penetrated = player_data.get('performance').get('shots_pen')
            enemies_destroyed = player_data.get(
                'performance').get('enemies_destroyed')
            time_alive = player_data.get('performance').get('time_alive')
            damage_blocked = player_data.get(
                'performance').get('damage_blocked')
            distance_travelled = player_data.get(
                'performance').get('distance_travelled')
            damage_assisted = player_data.get(
                'performance').get('damage_assisted')
            damage_assisted_track = player_data.get(
                'performance').get('damage_assisted_track')
            damage_made = player_data.get('performance').get('damage_made')
            kills = player_data.get('performance').get('enemies_destroyed')

            tank_hp = 2000
            travel_avg = 1000

            player_id = player
            platoon_number = player_data.get('performance').get('squad_index')
            survived_bool = True

            damage_efficiency = (damage_made + damage_assisted) / tank_hp
            kill_efficiency = kills / 7
            travel_efficiency = distance_travelled / (travel_avg or 1)
            shot_efficiency = (shots_penetrated) / \
                (shots_fired or 1)

            rating = round(((damage_efficiency + kill_efficiency +
                             travel_efficiency + shot_efficiency) / 4 * 1000))

            player_data['rating'] = rating

        return self.replay_data
