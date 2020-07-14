from operator import itemgetter
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from discord import File
from io import BytesIO


class Render():
    def __init__(self, replay_data, replay_id, stats=None, stats_bottom=None):

        # Stats to include for each player by default
        if not stats:
            stats = ['kills', 'damage', 'player_wr', 'rating']
        if not stats_bottom:
            stats_bottom = ['kills', 'damage', 'player_wr', 'rating']

        self.stats = stats
        self.stats_bottom = stats_bottom

        self.replay_data = replay_data
        self.battle_summary = self.replay_data.get(
            'battle_summary')
        self.replay_id = replay_id

        # Replay Details
        self.battle_result_num = self.battle_summary.get('battle_result')
        self.map_name = self.replay_data.get('battle_summary').get('map_name')
        self.battle_start_time = self.battle_summary.get(
            'battle_start_timestamp')

        self.room_type = self.battle_summary.get('room_type')
        self.winner_team = self.battle_summary.get('winner_team')

        self.battle_result = 'Defeat'
        if self.battle_result_num == 1:
            self.battle_result = 'Victory'
        if self.battle_result_num == 2:
            self.battle_result = 'Draw'

        # Protagonist performance
        self.protagonist_id = self.battle_summary.get('protagonist')
        self.protagonist_data = self.replay_data.get(
            'players').get(self.protagonist_id)
        protagonist_data = self.replay_data.get(
            'players').get(str(self.protagonist_id))
        self.protagonist_name = self.replay_data.get(
            'players').get(str(self.protagonist_id)).get('nickname')
        self.protagonist_team = self.replay_data.get(
            'players').get(str(self.protagonist_id)).get('team')

        self.pr_performance = protagonist_data.get('performance')
        self.pr_vehicle_stats = protagonist_data.get('vehicle_stats')
        self.pr_vehicle_name = self.replay_data.get('players').get(
            str(self.protagonist_id)).get('player_vehicle_name')
        self.pr_vehicle_type = self.replay_data.get('players').get(
            str(self.protagonist_id)).get('player_vehicle_type')
        self.pr_vehicle_tier = self.replay_data.get('players').get(
            str(self.protagonist_id)).get('player_vehicle_tier')

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

        self.all_players = []
        self.allies_render = []
        self.enemies_render = []

        self.best_rating = 0
        self.longest_stat = 0
        self.longest_stat_bottom = 0
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

            if self.best_rating < data.get('rating_value'):
                self.best_rating = data.get('rating_value')

            for stat in self.stats:
                if len(f'{self.longest_stat}') < len(f'{data.get(stat)}'):
                    self.longest_stat = player.get(stat)

            for stat in self.stats_bottom:
                if len(f'{self.longest_stat_bottom}') < len(f'{data.get(stat)}'):
                    self.longest_stat_bottom = player.get(stat)

            if len(self.longest_name) < len(data.get('nickname') + f'{ [clan_tag]}'):
                self.longest_name = data.get('nickname') + f'{ [clan_tag]}'

            if len(self.longest_clan) < len(clan_tag):
                self.longest_clan = clan_tag

            if data.get('team') == 2:
                self.enemies_render.append(player)
                self.all_players.append(player)
                self.enemy_rating_total += player.get('rating_value')
            else:
                self.allies_render.append(player)
                self.all_players.append(player)
                self.ally_rating_total += player.get('rating_value')

    def image(self, bg=1, brand=1, darken=1, mapname=1):
        """
        bg - Draw background image \n
        brand - Draw branding \n
        darken - Draw dark bg overlay \n
        mapname - Draw map name and result \n
        """
        frame_w = 1100
        frame_h = 640

        frame = Image.new('RGBA', (frame_w, frame_h), (0, 0, 0, 0))
        self.image = frame
        self.draw_frame = ImageDraw.Draw(self.image)
        self.platoon_image = Image.open(
            './cogs/replays/render/icons/platoon.png')

        self.font_size = 16

        self.text_margin_w = self.font_size
        self.text_margin_h = 5

        self.image_w, self.image_h = frame.size
        # Will bhe devided by 2
        self.platoon_icon_margin = 28
        # Height of each player card
        self.image_step = 54

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
            "./cogs/replays/render/fonts/font.ttf", self.font_size)
        self.font_fat = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_fat.ttf", (round(self.font_size * 1.25)))
        self.font_slim = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_slim.ttf", self.font_size)
        self.font_title = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", (self.font_size * 5))
        self.font_platoon = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_slim.ttf", 12)
        self.team_rating_font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", 18)
        self.bottom_stats_font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_fat.ttf", round(self.font_size))

        # Width of each player card
        longest_name, _ = self.draw_frame.textsize(
            self.longest_name, self.font)
        longest_stat, _ = self.draw_frame.textsize(
            f'{self.longest_stat}', self.font)

        self.player_card_w = round(
            (self.platoon_icon_margin) + longest_name + (self.text_margin_w * 2) + (longest_stat * len(self.stats)))

        # Margin from frame border
        self.image_min_w = round((self.image_w - (self.player_card_w * 2)) / 3)

        self.enemy_team_offset_w = self.image_w - \
            (self.image_min_w)-(self.player_card_w)

        if bg == 1:
            solid_bg = Image.new('RGB', (frame_w, frame_h), (0, 0, 0))
            try:
                bg_image = Image.open(
                    f'./cogs/replays/render/bg_frames_named/{self.protagonist_id}.jpg')
            except:
                bg_image = Image.open('./cogs/replays/render/bg_frame.png')

            bg_image_w, bg_image_h = bg_image.size
            bg_image_ratio = frame_h / bg_image_h
            if bg_image_ratio < frame_w / bg_image_w:
                bg_image_ratio = frame_w / bg_image_w
            bg_image = bg_image.resize(
                (int(bg_image_w * bg_image_ratio), int(bg_image_h * bg_image_ratio)))
            solid_bg.paste(bg_image, box=(
                0, 0))
            self.image = solid_bg
            self.draw_frame = ImageDraw.Draw(self.image)

        if mapname == 0:
            self.image_min_h = round(
                (self.image_h - (int(len(self.all_players) / 2) + 2) * (self.image_step)) / 2)

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

            self.image_min_h = round(result_text_h + self.image_step)

            battle_result_draw_w = round((self.image_w - result_text_w) / 2)
            battle_result_draw_h = round(
                (self.image_min_h - result_text_h) / 2)

            self.draw_frame.text((battle_result_draw_w, battle_result_draw_h), battle_result_str,
                                 fill=result_font_color, font=self.font_title)

        self.global_stat_max_width = {
            'kills': 0,
            'damage': 0,
            'player_wr': 0,
            'rating': 0,
            'credits_total': 0,
            'exp_total': 0,
        }

        self.teams = [self.enemies_render, self.allies_render]

        self.draw_ui_all()

        for player_list in self.teams:
            step = 1
            team_rating = 0
            team_offset_w = self.image_min_w
            if player_list[0].get('team') == 2:
                team_offset_w = self.enemy_team_offset_w

            for player in player_list:
                team_rating += int(player.get('rating_value'))
                player_card = self.draw_player_card(player)
                plate_w_pos = round(team_offset_w)
                plate_h_pos = round(self.image_min_h +
                                    (self.image_step * (step)))

                self.image.paste(player_card, box=(
                    plate_w_pos, plate_h_pos), mask=player_card.split()[3])
                step += 1
                if step >= 8:
                    break

            step = 0

            self.draw_top_ui_self(team_rating, team_offset_w)

        final_buffer = BytesIO()
        self.image.save(final_buffer, 'png')
        final_buffer.seek(0)
        image_file = File(
            filename=f"result.png", fp=final_buffer)

        return image_file

    def draw_ui_all(self):
        team_card_w = (self.player_card_w * 2) + self.image_min_w
        team_card_h = self.image_step - (self.text_margin_h * 2)

        # Draw top team card
        team_card_top = Image.new(
            'RGBA', (team_card_w, (team_card_h)), (51, 51, 51, 255))
        team_card_w, team_card_h = team_card_top.size
        top_card_draw_w = self.image_min_w
        top_card_draw_h = self.image_min_h
        self.image.paste(team_card_top, box=(
            top_card_draw_w, top_card_draw_h), mask=team_card_top.split()[3])

        # Draw bottom team card
        team_card_bot = Image.new(
            'RGBA', (team_card_w, (team_card_h)), (51, 51, 51, 255))
        bot_team_card_w, bot_team_card_h = team_card_bot.size
        bot_card_draw_w = self.image_min_w
        bot_card_draw_h = self.image_min_h + \
            (self.image_step * ((int(len(self.all_players) / 2) + 1)))

        # Draw bottom battle results
        draw_bot = ImageDraw.Draw(team_card_bot)

        # Get map name and battle result text sizes
        map_name_w, map_name_h = draw_bot.textsize(
            self.map_name, font=self.font)
        battle_result_w, battle_result_h = draw_bot.textsize(
            self.battle_result, font=self.font)

        # Get battle start time text sizes
        battle_date, battle_time = self.battle_start_time.split(' ')
        battle_date_w, battle_date_h = draw_bot.textsize(
            battle_date, font=self.font)
        battle_time_w, battle_time_h = draw_bot.textsize(
            battle_time, font=self.font)

        battle_date_draw_w = team_card_w - self.platoon_icon_margin - battle_date_w
        battle_time_draw_w = team_card_w - self.platoon_icon_margin - battle_time_w
        battle_date_draw_h = (
            bot_team_card_h - battle_date_h - battle_time_h) / 3
        battle_time_draw_h = (battle_date_draw_h * 2) + battle_date_h

        map_name_draw_w = battle_result_draw_w = self.platoon_icon_margin
        battle_result_draw_h = (
            bot_team_card_h - map_name_h - battle_result_h) / 3
        map_name_draw_h = (battle_result_draw_h * 2) + battle_result_h

        draw_bot.text((battle_date_draw_w, battle_date_draw_h), battle_date,
                      self.font_color_base, font=self.font)
        draw_bot.text((battle_time_draw_w, battle_time_draw_h), battle_time,
                      self.font_color_base, font=self.font)

        draw_bot.text((battle_result_draw_w, battle_result_draw_h), self.battle_result,
                      self.font_color_base, font=self.font)
        draw_bot.text((map_name_draw_w, map_name_draw_h), self.map_name,
                      self.font_color_base, font=self.font)

        protagonist_card_unique = Image.new(
            'RGBA', (self.player_card_w, (self.image_step - 10)), (0, 0, 0, 0))
        protagonist_card_w, protagonist_card_h = protagonist_card_unique.size
        draw_bot_pr_card = ImageDraw.Draw(protagonist_card_unique)

        bottom_icons = ['credits_total', 'exp_total']

        last_icon_pos = 0
        for icon in bottom_icons:
            icon_name = icon
            icon_value = self.battle_summary.get(icon_name)
            icon_size = round(team_card_h / 2)
            stat_value = str(self.battle_summary.get(icon))

            icon = Image.open(f'./cogs/replays/render/icons/{icon_name}.png')
            icon = icon.resize((icon_size, icon_size))
            icon_w, icon_h = icon.size
            stat_text_w, stat_text_h = draw_bot.textsize(
                stat_value, font=self.bottom_stats_font)

            # In case multiple rows need to be added
            max_width = self.global_stat_max_width.get(icon_name)
            icon_budle_width = icon_w + stat_text_w + (self.text_margin_w)

            icon_draw_w = last_icon_pos
            icon_draw_h = round((protagonist_card_h - icon_h) / 2)

            stat_text_draw_w = icon_draw_w + icon_w + (icon_w / 4)
            stat_text_draw_h = round((protagonist_card_h - stat_text_h) / 2)

            protagonist_card_unique.paste(icon, box=(
                icon_draw_w, icon_draw_h), mask=icon.split()[3])
            draw_bot_pr_card.text((stat_text_draw_w, stat_text_draw_h), stat_value,
                                  self.font_color_base, font=self.bottom_stats_font)

            last_icon_pos += icon_budle_width + icon_w

        # Add bottom card to UI
        protagonist_card_draw_w = round(
            (bot_team_card_w - last_icon_pos) / 2)
        protagonist_card_draw_h = 0

        team_card_bot.paste(protagonist_card_unique, box=(
            protagonist_card_draw_w, protagonist_card_draw_h), mask=protagonist_card_unique.split()[3])
        self.image.paste(team_card_bot, box=(
            bot_card_draw_w, bot_card_draw_h), mask=team_card_bot.split()[3])
        return

    def draw_top_ui_self(self, rating_total, team_offs):
        card_height = self.image_step - (self.text_margin_h * 2)
        card_width = self.player_card_w

        team_card = Image.new(
            'RGBA', (card_width, (card_height)), (51, 51, 51, 255))
        team_card_w, team_card_h = team_card.size

        icon_frame_w = icon_frame_h = round(
            (card_height * 2 / 3) - self.text_margin_h)

        player_list = Image.open(
            f'./cogs/replays/render/icons/player_list.png')
        player_list = player_list.resize((icon_frame_w, icon_frame_h))
        player_list_w, player_list_h = player_list.size

        card_draw_w = team_offs
        card_draw_h = self.image_min_h

        player_list_draw_w = self.platoon_icon_margin
        icons_draw_h = round((team_card_h - player_list_h) / 2)

        team_card.paste(player_list, box=(
            player_list_draw_w, icons_draw_h), mask=player_list.split()[3])

        last_stat_pos = 0
        for icon in self.stats:
            icon_name = icon
            icon = Image.open(f'./cogs/replays/render/icons/{icon_name}.png')
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
        rating_value = player.get('rating_value')
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

        clan_str = f'[{clan}]'
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
            hero_icon = Image.open(
                f'./cogs/replays/render/icons/hero_icon.png')
            hero_icon = hero_icon.resize((self.font_size, self.font_size))
            hero_icon_w = round(tank_draw_w + self.text_margin_w + tank_text_w)
            hero_icon_h = self.text_margin_h + 1

            player_card.paste(hero_icon, box=(
                hero_icon_w, hero_icon_h), mask=hero_icon.split()[3])

        # Render performance stats
        for stat in self.stats:
            stat_font = self.get_font(f'{stat}')
            stat_str = f'{player.get(stat)}'
            text_w, _ = draw.textsize(stat_str, font=stat_font)

            if stat in self.global_stat_max_width.keys() and text_w > self.global_stat_max_width.get(stat):
                self.global_stat_max_width[stat] = text_w

        last_stat_pos = 0
        for stat in self.stats:
            stat_value = player.get(stat)
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
                rating_percent = rating_value / self.best_rating * 100
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
