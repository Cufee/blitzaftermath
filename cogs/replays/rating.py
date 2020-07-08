class Rating:
    def __init__(self, replays_data):
        self.replay_data = replay_data[0]
        self.replay_summary = self.replay_data.get('summary')
        self.replay_players = self.replay_data.get('players')

    def restructure_data(self):
        replay_details = self.replay_summary.get('details')
        all_vehicles = []
        for player in replay_details:
            # Player info
            player_id = player.get('dbid')
            vehicle = player.get('vehicle_descr')
            all_vehicles.append(vehicle)
            platoon_number = player.get('squad_index')
            survived_bool = True
            if player.get('hitpoints_left') == 0:
                survived_bool = False

            # Performance
            shots_fired = player.get('shots_made')
            shots_penetrated = player.get('shots_pen')
            enemies_destroyed = player.get('enemies_destroyed')
            time_alive = player.get('time_alive')
            damage_blocked = player.get('damage_blocked')
            distance_travelled = player.get('distance_travelled')
            damage_assisted = player.get('damage_assisted')
            damage_assisted_track = player.get('damage_assisted_track')
            damage_made = player.get('damage_made')

            player_rating = ''
