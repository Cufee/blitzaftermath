from operator import itemgetter


class Render():
    def __init__(self, replay_data, replay_id):
        self.replay_data = replay_data
        self.replay_id = replay_id

        # Player details
        self.map_name = self.replay_data.get('battle_summary').get('map_name')
        self.winner_team = self.replay_data.get(
            'battle_summary').get('winner_team')

        self.protagonist_id = self.replay_data.get(
            'battle_summary').get('protagonist')
        protagonist_data = self.replay_data.get(
            'players').get(str(self.protagonist_id))
        self.protagonist_name = self.replay_data.get(
            'players').get(str(self.protagonist_id)).get('nickname')

        self.battle_result = 'Victory'
        if self.winner_team != 1:
            self.battle_result = 'Defeat'

        self.all_names_render = []
        self.allies_names = []
        self.allies_render = []
        self.enemies_names = []
        self.enemies_render = []
        self.all_names = []

        self.best_rating = 0
        self.ally_rating_total = 0
        self.enemy_rating_total = 0

        players_data = self.replay_data.get('players')
        players_data = sorted(
            players_data.values(), key=itemgetter('rating'), reverse=True)

        for player in players_data:
            data = player

            if self.best_rating < data.get('rating'):
                self.best_rating = data.get('rating')

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
                'damage': data.get('performance').get('damage_made'),
                'kills': data.get('performance').get('enemies_destroyed'),
                'team': data.get('team'),
                'platoon_str': platoon_str,
                'nickname': data.get('nickname'),
                'clan_tag': clan_tag,
                'player_vehicle': player_vehicle,
                'vehicle_battles': vehicle_battles,
                'vehicle_wr': vehicle_wr,
                'player_wr': player_wr,
            }

            self.all_names_render.append(player_render_data)

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

        from discord import File

        import sys
        from io import BytesIO

        images = []
        image = Image.open('./cogs/replays/render/frame.png')
        draw = ImageDraw.Draw(image)

        font_size = 16
        font = ImageFont.truetype("./cogs/replays/render/font.ttf", font_size)
        font_title = ImageFont.truetype(
            "./cogs/replays/render/font.ttf", (font_size * 3))
        font_fat = ImageFont.truetype(
            "./cogs/replays/render/font_fat.ttf", (round(font_size * 1.25)))
        font_slim = ImageFont.truetype(
            "./cogs/replays/render/font_slim.ttf", font_size)
        font_slim_title = ImageFont.truetype(
            "./cogs/replays/render/font_slim.ttf", (font_size * 3))
        font_color_base = (255, 255, 255)
        font_color_nickname = (255, 255, 255)
        font_color_clan = (150, 150, 150)
        font_color_pr = (255, 165, 0)
        font_color_win = (95, 227, 66)
        font_color_loss = (242, 94, 61)

        team_rating_font = ImageFont.truetype(
            "./cogs/replays/render/font.ttf", 18)

        self.image_w, image_h = image.size
        self.image_min_w = 12 + font_size
        self.image_max_w = 516 - 12
        self.image_min_h = 150
        self.image_team_min_h = 100
        self.image_team_min_w = 135

        self.image_rating_min_w = 326
        self.image_rating_max_w = 372
        self.image_wr_min_w = 384
        self.image_wr_max_w = 430
        self.image_dmg_min_w = 430
        self.image_dmg_max_w = 486
        self.image_kills_min_w = 496
        self.image_kills_max_w = 508

        self.image_step = 54

        all_players = [self.enemies_render, self.allies_render]

        for player_list in all_players:
            step = 0
            team_rating = 0
            for player in player_list:
                rating = player.get('rating')
                damage = player.get('damage')
                kills = player.get('kills')
                platoon = player.get('platoon_str')
                team = player.get('team')
                nickname = player.get('nickname')
                player_wr = player.get('player_wr')
                clan = player.get('clan_tag')
                vehicle = player.get('player_vehicle')
                vehicle_battles = player.get('vehicle_battles')
                vehicle_wr = player.get('vehicle_wr')

                team_rating += int(rating)

                team_offset_w = 0
                if team == 2:
                    team_offset_w = 534

                team_offset_h = self.image_step

                # Draw platoons
                platoon_str = f'{platoon}'
                text_w, text_h = draw.textsize(platoon_str, font=font)
                text_margin = (self.image_step - (text_h * 2)) / 3
                platoon_margin = text_h + self.image_min_w

                draw_w = self.image_min_w + team_offset_w
                draw_h = self.image_min_h + \
                    ((self.image_step - text_h) / 3) + \
                    (self.image_step * step)
                draw.text((draw_w, draw_h), platoon_str,
                          font_color_base, font=font)

                # Draw tank
                vehicle_str = f'{vehicle}'
                text_w, text_h = draw.textsize(vehicle_str, font=font_slim)
                text_margin = (self.image_step - (text_h * 2)) / 3
                platoon_margin = text_h + text_margin

                draw_w = self.image_min_w + platoon_margin + team_offset_w
                draw_h = self.image_min_h + \
                    (self.image_step * step)
                draw.text((draw_w, draw_h), vehicle_str,
                          font_color_base, font=font_slim)

                # Draw name and clan
                font_color_nickname_fixed = font_color_nickname
                if nickname == self.protagonist_name:
                    font_color_nickname_fixed = font_color_pr

                name_str = f'{nickname} {clan}'
                text_w, text_h = draw.textsize(name_str, font=font)
                text_margin = (self.image_step - (text_h * 2)) / 3
                draw_h = self.image_min_h + text_h + \
                    (self.image_step * step)
                draw.text((draw_w, draw_h), name_str,
                          font_color_nickname_fixed, font=font)

                # Draw rating
                rating_str = f'{rating}'
                text_w, text_h = draw.textsize(rating_str, font=font_fat)
                text_margin = (self.image_step - (text_h * 2)) / 3
                draw_w = (self.image_rating_min_w) + ((self.image_rating_max_w -
                                                       self.image_rating_min_w - text_w) / 2) + team_offset_w
                draw_h = self.image_min_h + \
                    ((self.image_step - text_h) / 3) + \
                    (self.image_step * step)
                draw.text((draw_w, draw_h), rating_str,
                          font_color_base, font=font_fat)

                # Draw winrate
                player_wr_str = f'{player_wr}'
                text_w, text_h = draw.textsize(player_wr_str, font=font_slim)
                text_margin = (self.image_step - (text_h * 2)) / 3
                draw_w = (self.image_wr_min_w) + ((self.image_wr_max_w -
                                                   self.image_wr_min_w - text_w) / 2) + team_offset_w
                draw_h = self.image_min_h + \
                    ((self.image_step - text_h) / 3) + \
                    (self.image_step * step)
                draw.text((draw_w, draw_h), player_wr_str,
                          font_color_base, font=font_slim)

                # Draw damage
                damage_str = f'{damage}'
                text_w, text_h = draw.textsize(damage_str, font=font_slim)
                text_margin = (self.image_step - (text_h * 2)) / 3
                draw_w = (self.image_dmg_min_w) + ((self.image_dmg_max_w -
                                                    self.image_dmg_min_w - text_w) / 2) + team_offset_w
                draw_h = self.image_min_h + \
                    ((self.image_step - text_h) / 3) + \
                    (self.image_step * step)
                draw.text((draw_w, draw_h), damage_str,
                          font_color_base, font=font_slim)

                # Draw kills
                kills_str = f'{kills}'
                text_w, text_h = draw.textsize(kills_str, font=font_slim)
                text_margin = (self.image_step - (text_h * 2)) / 3
                draw_w = (self.image_kills_min_w) + ((self.image_kills_max_w -
                                                      self.image_kills_min_w - text_w) / 2) + team_offset_w
                draw_h = self.image_min_h + \
                    ((self.image_step - text_h) / 3) + \
                    (self.image_step * step)
                draw.text((draw_w, draw_h), kills_str,
                          font_color_base, font=font_slim)

                # Not working, needs a fix
                # draw.line(((self.image_min_w + team_offset_w), (self.image_step * (step + 1) + text_margin),
                #            (self.image_min_w + team_offset_w), (self.image_step * (step + 1) + text_margin)), fill=0, width=1)

                step += 1
                if step >= 7:
                    break

            # Draw team rating
            team_rating_str = f'{team_rating}'
            text_w, text_h = draw.textsize(team_rating_str, font=font)
            text_margin = (self.image_step - (text_h * 2)) / 3
            draw_w = self.image_team_min_w + text_h + team_offset_w
            draw_h = self.image_team_min_h
            draw.text((draw_w, draw_h), team_rating_str,
                      font_color_base, font=team_rating_font)

            font_color_result = font_color_win
            if self.winner_team != 1:
                font_color_result = font_color_loss

            # Draw map name and result
            map_pos_h = 40
            map_pos_w = self.image_w / 2
            map_name_str = f'{self.map_name} - {self.battle_result}'
            text_w, text_h = draw.textsize(map_name_str, font=font_slim_title)
            text_margin = (self.image_step - (text_h * 2)) / 3
            draw_w = map_pos_w - (text_w / 2)
            draw_h = map_pos_h - (text_h / 2)
            draw.text((draw_w, draw_h), map_name_str,
                      font_color_base, font=font_slim_title)
            step = 0

        final_buffer = BytesIO()
        image.save(final_buffer, 'png')
        final_buffer.seek(0)
        image_file = File(
            filename=f"result.png", fp=final_buffer)

        return image_file

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

    def get_color(self, key, value=None):
        colors = {
            'rating': {
                'purple': '#a61a95',
                'blue': '#3972c6',
                'green': '#4d7326',
                'yellow': '#ffbf01',
                'red': '#c20000',
            },
            'winrate': {
                'purple': '#a61a95',
                'blue': '#3972c6',
                'green': '#4d7326',
                'yellow': '#ffbf01',
                'red': '#c20000',
            },
            'clan': '#FFA500',
            'platoon': '#FE9B04',
            'primary': '#5A5A5A',
        }

        if value:
            hex_color = colors.get(key).get(value)
        else:
            hex_color = colors.get(key) or colors.get('primary')

        hex_color.lstrip('#')
        rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        return rgb_color
