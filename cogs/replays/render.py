from discord import Embed
from operator import itemgetter


class Render():
    def __init__(self, replay_data, replay_id):
        self.replay_data = replay_data
        self.replay_id = replay_id

    def embed(self):
        map_name = self.replay_data.get('battle_summary').get('map_name')
        winner_team = self.replay_data.get('battle_summary').get('winner_team')

        protagonist_id = self.replay_data.get(
            'battle_summary').get('protagonist')
        protagonist_data = self.replay_data.get(
            'players').get(str(protagonist_id))
        protagonist_name = self.replay_data.get(
            'players').get(str(protagonist_id)).get('nickname')

        battle_result = 'Win'
        if winner_team != 1:
            battle_result = 'Loss'

        allies_names = []
        enemies_names = []
        all_names = []

        best_rating = 0
        ally_rating_total = 0
        enemy_rating_total = 0

        players_data = self.replay_data.get('players')

        players_data = sorted(
            players_data.values(), key=itemgetter('rating'), reverse=True)

        for player in players_data:
            data = player

            if best_rating < data.get('rating'):
                best_rating = data.get('rating')

            player_wins = data.get('stats').get('wins')
            player_battles = data.get('stats').get('battles')
            player_vehicle = data.get('vehicle').get('name')
            player_vehicle_type = data.get('vehicle').get('type')

            try:
                vehicle_wins = data.get('vehicle_stats').get('wins')
                vehicle_battles = data.get('vehicle_stats').get('battles')
                vehicle_wr = "%.2f" % round(
                    (vehicle_wins / vehicle_battles * 100), 2) + '%'
            except:
                vehicle_wins = 0
                vehicle_battles = 0
                vehicle_wr = '0%'

            player_wr = "%.2f" % round(
                (player_wins / player_battles * 100), 2) + '%'

            platoon_number = data.get('performance').get('squad_index')
            platoon_str = ''
            if platoon_number:
                platoon_str = f'[{platoon_number}]'

            player_final_str = (
                f"[{data.get('rating')}] {platoon_str}{data.get('nickname')} - {player_vehicle}\nWR: {player_wr} Tank WR: {vehicle_wr} ({vehicle_battles})")

            all_names.append(player_final_str)

            if data.get('team') == 2:
                enemies_names.append(player_final_str)
                enemy_rating_total += data.get('rating')
            else:
                allies_names.append(player_final_str)
                ally_rating_total += data.get('rating')

        # Protagonist performance
        pr_performance = protagonist_data.get('performance')
        pr_vehicle_stats = protagonist_data.get('vehicle_stats')
        pr_vehicle_name = protagonist_data.get('vehicle').get('name')
        pr_vehicle_type = protagonist_data.get('vehicle').get('type')

        pr_battle_dmg = pr_performance.get(
            'damage_made')
        pr_stats_avg_dmg = round(pr_vehicle_stats.get(
            'damage_dealt') / (pr_vehicle_stats.get('battles') or 1))

        pr_battle_kills = pr_performance.get(
            'enemies_destroyed')
        pr_stats_avg_kills = round(pr_vehicle_stats.get(
            'frags8p') / (pr_vehicle_stats.get('battles') or 1))

        pr_battle_shots = pr_performance.get(
            'shots_made')
        pr_battle_pen = pr_performance.get(
            'shots_pen')

        embed_stats_text = (
            f'Damage vs Career {pr_battle_dmg}/{pr_stats_avg_dmg}\n' +
            f'Kills vs Career {pr_battle_kills}/{pr_stats_avg_kills}\n' +
            f'Shots vs Pen {pr_battle_shots}/{pr_battle_pen}\n' +
            f'')

        # Defining Embed
        embed_key = f'[WR] [Vehicle WR (Battles)] [vRT] Nickname'
        embed_allies = (' \n\n'.join(allies_names))
        embed_enemies = (' \n\n'.join(enemies_names))
        embed_all_players = (' \n\n'.join(all_names))
        embed_stats = embed_stats_text

        embed_footer = f"MD5/ID: {self.replay_id}"

        replay_link = 'https://www.google.com/'

        # Constructing Embed
        embed = Embed(
            title="Click here for detailed results", url=replay_link)
        embed.set_author(
            name=f"Battle by {protagonist_name} on {map_name}")
        # embed.add_field(
        #     name='Legend', value=f'```{embed_key}```', inline=False)
        embed.add_field(
            name=f'Allies [{ally_rating_total}]', value=f'```{embed_allies} ```', inline=False)
        embed.add_field(
            name=f'Enemies [{enemy_rating_total}]', value=f'```{embed_enemies} ```', inline=False)
        # embed.add_field(
        #     name='Players', value=f'```{embed_all_players} ```', inline=False)
        embed.add_field(
            name=f'{protagonist_name} - {pr_vehicle_name}', value=f'```{embed_stats}```', inline=False)
        embed.set_footer(text=embed_footer)

        return embed
