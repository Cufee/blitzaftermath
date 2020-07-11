from operator import itemgetter


class Render():
    def __init__(self, replay_data, replay_id):
        self.replay_data = replay_data
        self.replay_id = replay_id

        # Player details
        self.map_name = self.replay_data.get('battle_summary').get('map_name')
        winner_team = self.replay_data.get(
            'battle_summary').get('winner_team')

        protagonist_id = self.replay_data.get(
            'battle_summary').get('protagonist')
        protagonist_data = self.replay_data.get(
            'players').get(str(protagonist_id))
        self.protagonist_name = self.replay_data.get(
            'players').get(str(protagonist_id)).get('nickname')

        self.battle_result = 'Win'
        if winner_team != 1:
            self.battle_result = 'Loss'

        self.allies_names = []
        self.allies_render = []
        self.enemies_names = []
        self.enemies_render = []
        self.all_names = []

        best_rating = 0
        self.ally_rating_total = 0
        self.enemy_rating_total = 0

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

            clan_tag = ''
            if data.get('clan_tag'):
                clan_tag = f'[{data.get("clan_tag")}]'

            platoon_number = data.get('performance').get('squad_index')
            platoon_str = ''
            if platoon_number:
                platoon_str = f'[{platoon_number}]'

            player_final_str = (
                f"[{data.get('rating')}] {platoon_str} {data.get('nickname')}{clan_tag} - {player_vehicle}\nWR: {player_wr} Tank WR: {vehicle_wr} ({vehicle_battles})")

            self.all_names.append(player_final_str)

            player_render_data = {
                'rating': data.get('rating'),
                'platoon_str': platoon_str,
                'nickname': data.get('nickname'),
                'clan_tag': clan_tag,
                'player_vehicle': player_vehicle,
                'vehicle_battles': vehicle_battles,
                'vehicle_wr': vehicle_wr,
                'player_wr': player_wr,
            }

            if data.get('team') == 2:
                self.enemies_names.append(player_final_str)
                self.allies_render.append(player_render_data)
                self.enemy_rating_total += data.get('rating')
            else:
                self.allies_names.append(player_final_str)
                self.enemies_render.append(player_render_data)
                self.ally_rating_total += data.get('rating')

        # Protagonist performance
        self.pr_performance = protagonist_data.get('performance')
        self.pr_vehicle_stats = protagonist_data.get('vehicle_stats')
        self.pr_vehicle_name = protagonist_data.get('vehicle').get('name')
        self.pr_vehicle_type = protagonist_data.get('vehicle').get('type')

        self.pr_battle_dmg = self.pr_performance.get(
            'damage_made')
        self.pr_stats_avg_dmg = round(self.pr_vehicle_stats.get(
            'damage_dealt') / (self.pr_vehicle_stats.get('battles') or 1))

        self.pr_battle_kills = self.pr_performance.get(
            'enemies_destroyed')
        self.pr_stats_avg_kills = round(self.pr_vehicle_stats.get(
            'frags8p') / (self.pr_vehicle_stats.get('battles') or 1))

        self.pr_battle_shots = self.pr_performance.get(
            'shots_made')
        self.pr_battle_pen = self.pr_performance.get(
            'shots_pen')

    def image(self):
        from PIL import Image
        from PIL import ImageFont
        from PIL import ImageDraw

        import sys
        from io import BytesIO

        text = ['Testing ____________', 'TESTING MORE\nText here']

        image = Image.open('./cogs/replays/render/frame.png')
        font = ImageFont.truetype("./cogs/replays/render/font.ttf", 28)
        font_color_base = (150, 150, 150)
        draw = ImageDraw.Draw(image)

        image_w, image_h = image.size
        image_min_w = 84
        image_rt_mid_w = 42
        image_step = image_h / 8

        step = 1
        for player in self.enemies_render:
            rating = str(player.get('rating'))
            platoon = player.get('platoon_str')
            nickname = player.get('nickname')
            player_wr = player.get('player_wr')
            clan = player.get('clan_tag')
            vehicle = player.get('player_vehicle')
            vehicle_battles = player.get('vehicle_battles')
            vehicle_wr = player.get('vehicle_wr')

            # Draw Rating
            text_w, text_h = draw.textsize(rating, font=font)
            draw.text(((image_rt_mid_w - (text_w / 2)), (((image_step - text_h) / 2) + ((image_step) * step))),
                      rating, font_color_base, font=font)

            # Draw Player name, platoon, vehicle
            player_info_top = f'{platoon} {nickname}{clan} - {vehicle}'
            player_info_bot = f'Winrate {player_wr}   Tank Winrate {vehicle_wr} ({vehicle_battles})'

            _, text_h = draw.textsize(player_info_top, font=font)
            draw.text(((image_min_w), (((image_step - text_h) / 4) + (step * image_step))),
                      player_info_top, font_color_base, font=font)

            _, text_h = draw.textsize(player_info_bot, font=font)
            draw.text(((image_min_w), ((((image_step - text_h) / 4)) + (step * image_step) + text_h)),
                      player_info_bot, font_color_base, font=font)

            step += 1
            if step > 7:
                break

        final_buffer = BytesIO()
        image.save(final_buffer, 'png')
        final_buffer.seek(0)

        return final_buffer

    def embed(self):
        from discord import Embed
        embed_stats_text = (
            f'Damage vs Career {self.pr_battle_dmg}/{self.pr_stats_avg_dmg}\n' +
            f'Kills vs Career {self.pr_battle_kills}/{self.pr_stats_avg_kills}\n' +
            f'Shots vs Pen {self.pr_battle_shots}/{self.pr_battle_pen}\n' +
            f'')

        # Defining Embed
        embed_key = f'[WR] [Vehicle WR (Battles)] [vRT] Nickname'
        embed_allies = (' \n\n'.join(self.allies_names))
        embed_enemies = (' \n\n'.join(self.enemies_names))
        embed_all_players = (' \n\n'.join(self.all_names))
        embed_stats = embed_stats_text

        embed_footer = f"MD5/ID: {self.replay_id}"

        replay_link = 'https://www.google.com/'

        # Constructing Embed
        embed = Embed(
            title="Click here for detailed results", url=replay_link)
        embed.set_author(
            name=f"Battle by {self.protagonist_name} on {self.map_name}")
        # embed.add_field(
        #     name='Legend', value=f'```{embed_key}```', inline=False)
        embed.add_field(
            name=f'Allies [{self.ally_rating_total}]', value=f'```{embed_allies} ```', inline=False)
        embed.add_field(
            name=f'Enemies [{self.enemy_rating_total}]', value=f'```{embed_enemies} ```', inline=False)
        # embed.add_field(
        #     name='Players', value=f'```{embed_all_players} ```', inline=False)
        embed.add_field(
            name=f'{self.protagonist_name} - {self.pr_vehicle_name}', value=f'```{embed_stats}```', inline=False)
        embed.set_footer(text=embed_footer)

        return embed
