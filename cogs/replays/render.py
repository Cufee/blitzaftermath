from operator import itemgetter
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from discord import File
from io import BytesIO


class Render():
    def __init__(self, replay_data, replay_id):
        self.replay_data = replay_data
        self.replay_id = replay_id

        # Player details
        self.map_name = self.replay_data.get('battle_summary').get('map_name')
        self.room_type = self.replay_data.get(
            'battle_summary').get('room_type')
        self.winner_team = self.replay_data.get(
            'battle_summary').get('winner_team')

        self.protagonist_id = self.replay_data.get(
            'battle_summary').get('protagonist')
        protagonist_data = self.replay_data.get(
            'players').get(str(self.protagonist_id))
        self.protagonist_name = self.replay_data.get(
            'players').get(str(self.protagonist_id)).get('nickname')
        self.protagonist_team = self.replay_data.get(
            'players').get(str(self.protagonist_id)).get('team')
        self.battle_result_num = self.replay_data.get(
            'battle_summary').get('battle_result')

        self.battle_result = 'Defeat'
        if self.battle_result_num == 1:
            self.battle_result = 'Victory'
        if self.battle_result_num == 2:
            self.battle_result = 'Draw'

        self.all_names_render = []
        self.allies_names = []
        self.allies_render = []
        self.enemies_names = []
        self.enemies_render = []
        self.all_names = []

        self.best_rating = 0
        self.longest_name = ''
        self.longest_clan = ''
        self.ally_rating_total = 0
        self.enemy_rating_total = 0

        players_data = self.replay_data.get('players')
        players_data = sorted(
            players_data.values(), key=itemgetter('rating'), reverse=True)

        for player in players_data:
            data = player

            clan_tag = ''
            if data.get('clan_tag'):
                clan_tag = f'[{data.get("clan_tag")}]'

            if self.best_rating < data.get('rating'):
                self.best_rating = data.get('rating')
            data = player

            if len(self.longest_name) < len(data.get('nickname')):
                self.longest_name = data.get('nickname')

            if len(self.longest_clan) < len(clan_tag):
                self.longest_clan = clan_tag

            player_wins = data.get('stats').get('wins')
            player_battles = data.get('stats').get('battles')
            player_vehicle = data.get('vehicle').get('name')
            player_vehicle_type = data.get('vehicle').get('type')
            hp_left = data.get('performance').get('hitpoints_left')
            survived = True
            if hp_left <= 0:
                survived = False

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
                platoon_str = f'{platoon_number}'

            player_final_str = (
                f"[{data.get('rating')}] {platoon_str} {data.get('nickname')}{clan_tag} - {player_vehicle}\nWR: {player_wr} Tank WR: {vehicle_wr} ({vehicle_battles})")

            self.all_names.append(player_final_str)

            player_render_data = {
                'rating': data.get('rating'),
                'damage': data.get('performance').get('damage_made'),
                'kills': data.get('performance').get('enemies_destroyed'),
                'team': data.get('team'),
                'survived': survived,
                'hero_bonus_exp': data.get('performance').get('hero_bonus_exp'),
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

    def image(self, bg=1, brand=1, darken=1, mapname=1):
        """
        bg - Draw background image \n
        brand - Draw branding \n
        darken - Draw dark bg overlay \n
        mapname - Draw map name and result \n
        """
        frame_w = 1100
        frame_h = 580

        frame = Image.new('RGB', (frame_w, frame_h), (0, 0, 0))
        self.image = frame
        self.draw_frame = ImageDraw.Draw(self.image)
        self.platoon_image = Image.open('./cogs/replays/render/platoon.png')

        self.font_size = 16

        self.image_w, self.image_h = frame.size
        # Will bhe devided by 2
        self.platoon_icon_margin = 28
        # Height of each player card
        self.image_step = 54
        # Margin from frame border
        self.image_min_h = 200

        self.text_margin_w = self.font_size
        self.text_margin_h = 5

        self.font_color_base = (255, 255, 255)
        self.font_color_nickname = (255, 255, 255)
        self.font_color_nickname_dead = (180, 180, 180)
        self.font_color_clan = (150, 150, 150)
        self.font_color_pr = (255, 165, 0)
        self.font_color_pr_dead = (204, 132, 0)
        self.font_color_win = (95, 227, 66)
        self.font_color_loss = (242, 94, 61)

        self.player_card_color = (80, 80, 80, 200)
        self.result_back_color = (80, 80, 80, 0)
        self.map_font_color = (110, 110, 110, 255)

        self.font = ImageFont.truetype(
            "./cogs/replays/render/font.ttf", self.font_size)
        self.font_fat = ImageFont.truetype(
            "./cogs/replays/render/font_fat.ttf", (round(self.font_size * 1.25)))
        self.font_slim = ImageFont.truetype(
            "./cogs/replays/render/font_slim.ttf", self.font_size)
        self.font_title = ImageFont.truetype(
            "./cogs/replays/render/font.ttf", (self.font_size * 5))
        self.font_platoon = ImageFont.truetype(
            "./cogs/replays/render/font_slim.ttf", 12)
        self.team_rating_font = ImageFont.truetype(
            "./cogs/replays/render/font.ttf", 18)

        # Width of each player card
        longest_name, _ = self.draw_frame.textsize(
            self.longest_name, self.font)
        longest_clan, _ = self.draw_frame.textsize(
            self.longest_clan, self.font)
        longest_rating, _ = self.draw_frame.textsize(
            f'{self.best_rating}', self.font)

        self.player_card_w = round(
            self.platoon_icon_margin + longest_name + longest_clan + (self.text_margin_w * 6) + (longest_rating * 5))

        # Margin from frame border
        self.image_min_w = round((self.image_w - (self.player_card_w * 2)) / 3)

        self.enemy_team_offset_w = self.image_w - \
            (self.image_min_w)-(self.player_card_w)

        if bg == 1:
            try:
                bg_image = Image.open(
                    f'./cogs/replays/render/bg_frames_named/{self.protagonist_id}.jpg')
            except:
                bg_image = Image.open('./cogs/replays/render/bg_frame.png')

            bg_image_w, bg_image_h = bg_image.size
            bg_image_ratio = frame_w / bg_image_w
            bg_image = bg_image.resize(
                (int(bg_image_w * bg_image_ratio), int(bg_image_h * bg_image_ratio)))
            frame.paste(bg_image, box=(
                0, 0))

        if mapname == 0:
            self.image_min_h = self.image_step

        if brand == 1:
            branding_w = int((frame_w - frame_w) / 2)
            branding_h = int((frame_h - frame_h) / 2)
            overlay_brand_am = Image.open(
                './cogs/replays/render/aftermath_frame.png')
            frame.paste(overlay_brand_am, box=(
                branding_w, branding_h), mask=overlay_brand_am.split()[3])

        if darken == 1:
            overlay_dark = Image.new(
                'RGBA', (frame_w, frame_h), (0, 0, 0, 128))
            frame.paste(overlay_dark, box=(
                0, 0), mask=overlay_dark.split()[3])

        if mapname == 1:
            # Draw battle result
            if self.battle_result_num == 0:
                result_font_color = self.font_color_loss
            if self.battle_result_num == 1:
                result_font_color = self.font_color_win
            if self.battle_result_num == 2:
                result_font_color = self.font_color_base

            battle_result_str = f'{self.battle_result}'
            result_text_w, result_text_h = self.draw_frame.textsize(
                battle_result_str, font=self.font_title)

            battle_result_draw_w = round((self.image_w - result_text_w) / 2)
            battle_result_draw_h = round(
                (self.image_min_h - self.image_step - result_text_h) / 2)

            self.draw_frame.text((battle_result_draw_w, battle_result_draw_h), battle_result_str,
                                 fill=result_font_color, font=self.font_title)

        self.global_stat_max_width = {
            'kills': 0,
            'damage': 0,
            'player_wr': 0,
            'rating': 0,
        }

        self.stats_list = ['kills', 'damage', 'player_wr', 'rating']

        all_players = [self.enemies_render, self.allies_render]
        for player_list in all_players:
            step = 0
            team_rating = 0
            team_offset_w = self.image_min_w
            if player_list[0].get('team') == 2:
                team_offset_w = self.enemy_team_offset_w

            for player in player_list:
                team_rating += int(player.get('rating'))
                player_card = self.draw_player_card(player)
                plate_w_pos = round(team_offset_w)
                plate_h_pos = round(self.image_min_h +
                                    (self.image_step * (step)))

                self.image.paste(player_card, box=(
                    plate_w_pos, plate_h_pos), mask=player_card.split()[3])
                step += 1
                if step >= 7:
                    break

            self.draw_ui_self(team_rating, team_offset_w)
            step = 0

        final_buffer = BytesIO()
        self.image.save(final_buffer, 'png')
        final_buffer.seek(0)
        image_file = File(
            filename=f"result.png", fp=final_buffer)

        return image_file

    def draw_ui_self(self, rating_total, team_offs):
        self.player_card_w
        self.text_margin_w

        card_height = self.image_step - self.text_margin_h

        team_card = Image.new(
            'RGBA', (self.player_card_w, (card_height)), (51, 51, 51, 255))
        team_card_w, team_card_h = team_card.size

        icon_frame_w = icon_frame_h = round(
            (card_height * 2 / 3) - self.text_margin_h)

        player_list = Image.open(f'./cogs/replays/render/player_list.png')
        player_list = player_list.resize((icon_frame_w, icon_frame_h))
        player_list_w, player_list_h = player_list.size

        card_draw_w = team_offs
        card_draw_h = self.image_min_h - card_height - (self.text_margin_h * 2)

        player_list_draw_w = self.platoon_icon_margin
        icons_draw_h = round((team_card_h - player_list_h) / 2)

        team_card.paste(player_list, box=(
            player_list_draw_w, icons_draw_h), mask=player_list.split()[3])

        last_stat_pos = 0
        for icon in self.stats_list:
            icon_name = icon
            icon = Image.open(f'./cogs/replays/render/{icon_name}.png')
            icon = icon.resize((icon_frame_w, icon_frame_h))
            icon_w, icon_h = icon.size
            max_width = self.global_stat_max_width.get(icon_name)

            draw_w = round(
                ((team_card_w - self.text_margin_w - max_width - last_stat_pos) + ((max_width - icon_w) / 2)))
            # draw_w = round(team_card_w)

            team_card.paste(icon, box=(
                draw_w, icons_draw_h), mask=icon.split()[3])
            last_stat_pos += max_width + self.text_margin_w

        self.image.paste(team_card, box=(
            (card_draw_w), card_draw_h), mask=team_card.split()[3])

        return

    def draw_player_card(self, player):
        """
        Renders a complete [player_card]
        """
        rating = player.get('rating')
        survived = player.get('survived')
        hero_bonus_exp = player.get('hero_bonus_exp')
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

        # Draw name bg plates
        player_card = Image.new(
            'RGBA', (self.player_card_w, (self.image_step - 10)), self.player_card_color)
        player_card_w, player_card_h = player_card.size

        draw = ImageDraw.Draw(player_card)

        # Draw platoons
        if platoon:
            platoon_font = self.font_platoon
            platoon_font_color = self.font_color_base
            platoon_img = self.platoon_image.copy()
            draw_platoon = ImageDraw.Draw(platoon_img)

            platoon_str = f'{platoon}'
            text_w, text_h = draw.textsize(platoon_str, font=platoon_font)
            platoon_img_w, platoon_img_h = self.platoon_image.size

            draw_w = round((platoon_img_w - text_w) / 2)
            draw_h = 0
            draw_platoon.text((draw_w, draw_h), platoon_str,
                              platoon_font_color, font=platoon_font)

            platoon_w_pos = round(
                (self.platoon_icon_margin - platoon_img_w) / 2)
            platoon_h_pos = round((player_card_h - platoon_img_h) / 2)
            player_card.paste(platoon_img, mask=self.platoon_image.split()[
                3], box=(platoon_w_pos, platoon_h_pos))

        # Render Tank, Player name, Clan
        tank_font = self.font
        name_font = self.font_slim
        font_color = self.font_color_base
        font_color_info = self.font_color_base
        font_color_name = self.font_color_base
        if not survived:
            font_color_info = self.font_color_nickname_dead
            font_color_name = self.font_color_nickname_dead
        if nickname == self.protagonist_name:
            font_color_name = self.font_color_pr
            if not survived:
                font_color_name = self.font_color_pr_dead

        clan_str = f'{clan}'
        tank_str = f'{vehicle}'
        name_str = f'{nickname}'
        tank_text_w, tank_text_h = draw.textsize(tank_str, font=tank_font)
        name_text_w, name_text_h = draw.textsize(name_str, font=name_font)
        clan_text_w, clan_text_h = draw.textsize(clan_str, font=name_font)

        draw_w = self.platoon_icon_margin
        tank_draw_w = self.platoon_icon_margin
        tank_draw_h = self.text_margin_h
        name_draw_w = self.platoon_icon_margin
        name_draw_h = round(
            (player_card_h - (tank_text_h + name_text_h + self.text_margin_h)) + tank_text_h)
        clan_draw_w = round(name_draw_w + name_text_w + (self.font_size / 2))
        clan_draw_h = name_draw_h

        draw.text((tank_draw_w, tank_draw_h), tank_str,
                  font_color_info, font=tank_font)
        draw.text((name_draw_w, name_draw_h), name_str,
                  font_color_name, font=name_font)
        draw.text((clan_draw_w, clan_draw_h), clan_str,
                  font_color_info, font=name_font)

        if hero_bonus_exp > 0:
            hero_icon = Image.open(f'./cogs/replays/render/hero_icon.png')
            hero_icon = hero_icon.resize((self.font_size, self.font_size))
            hero_icon_w = round(tank_draw_w + self.text_margin_w + tank_text_w)
            hero_icon_h = self.text_margin_h + 1

            player_card.paste(hero_icon, box=(
                hero_icon_w, hero_icon_h), mask=hero_icon.split()[3])

        stats = {
            'kills': {
                'value': kills,
                'max_width': 0,
            },
            'damage': {
                'value': damage,
                'max_width': 0,
            },
            'player_wr': {
                'value': player_wr,
                'max_width': 0,
            },
            'rating': {
                'value': rating,
                'max_width': 0,
            },
        }

        # Render performance stats
        for stat in stats:
            stat_font = self.get_font(f'{stat}')
            stat_str = f'{stats.get(stat).get("value")}'
            text_w, _ = draw.textsize(stat_str, font=stat_font)
            stat_max_width = stats.get(stat).get('max_width')
            stat_max_width_global = self.global_stat_max_width.get(stat)

            if text_w > stat_max_width_global:
                self.global_stat_max_width[stat] = text_w

        last_stat_pos = 0
        for stat in stats:
            stat_value = stats.get(stat).get("value")
            stat_max_width = self.global_stat_max_width.get(stat)
            stat_str = f'{stat_value}'

            stat_font = self.get_font(f'{stat}')
            stat_font_color = self.get_font(f'{stat}', 'color')
            if not survived:
                stat_font_color = font_color_info

            stat_text_w, stat_text_h = draw.textsize(
                stat_str, font=stat_font)

            stat_draw_w = round(
                ((player_card_w - self.text_margin_w - stat_max_width - last_stat_pos) + ((stat_max_width - stat_text_w) / 2)))
            stat_draw_h = round((player_card_h - stat_text_h) / 2)
            draw.text((stat_draw_w, stat_draw_h), stat_str,
                      stat_font_color, font=stat_font)

            if stat == 'rating':
                rating_percent = stat_value / self.best_rating * 100
                if rating_percent > 90:
                    stat_color = (201, 101, 219)
                elif rating_percent > 75:
                    stat_color = (101, 176, 219)
                elif rating_percent > 55:
                    stat_color = (123, 219, 101)
                elif rating_percent > 40:
                    stat_color = (219, 193, 101)
                else:
                    stat_color = (219, 109, 101)

                rating_box_w1 = round(
                    player_card_w - self.text_margin_w - stat_max_width - last_stat_pos) - self.text_margin_w
                rating_box_h1 = stat_draw_h
                rating_box_w2 = rating_box_w1 - 3
                rating_box_h2 = rating_box_h1 + stat_text_h + 1

                draw.rectangle([(rating_box_w1, rating_box_h1),
                                (rating_box_w2, rating_box_h2)], fill=stat_color)

            last_stat_pos += stat_max_width + self.text_margin_w

        return player_card

    def get_font(self, stat, color=None):
        rating_font = dmg_font = self.font
        wr_font = kills_font = self.font_slim
        font_color = self.font_color_base
        rating_font_color = self.font_color_base

        if color:
            return (255, 255, 255)

        return rating_font

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
