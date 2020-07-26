from operator import itemgetter
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from discord import File
from io import BytesIO

from re import compile, sub

from math import ceil, floor


class Render():
    def __init__(self, replay_data, replay_id, stats=None, stats_bottom=None):
        self.convert_to_num = compile(r'[^\d.]')

        self.replay_data = replay_data
        self.battle_summary = self.replay_data.get(
            'battle_summary')
        self.replay_id = replay_id
        self.room_type = self.battle_summary.get('room_type')
        self.room_type_str = f'({self.battle_summary.get("room_type_str")})'
        self.battle_type = self.battle_summary.get('battle_type')
        self.battle_type_str = self.battle_summary.get('battle_type_str')
        self.special_room_types = self.battle_summary.get(
            'special_room_types', [])

        # Disable some UI when in special battle modes, like Training rooms
        self.room_type_mod = 1
        if self.room_type in self.special_room_types:
            self.room_type_mod = 0

        if stats:
            self.stats = stats.copy()
            stats.reverse()
            self.stats_reversed = stats.copy()
        else:
            stats = ['rating', 'player_wr', 'damage_made', 'kills']
            self.stats = stats.copy()
            stats.reverse()
            self.stats_reversed = stats.copy()

        if stats_bottom:
            self.stats_bottom = stats_bottom
        elif not stats_bottom and self.room_type_mod == 1:
            self.stats_bottom = ['credits_total', 'exp_total']
        else:
            self.stats_bottom = []

        # Replay Details
        self.battle_result_num = self.battle_summary.get('battle_result')
        self.map_name = self.replay_data.get(
            'battle_summary').get('map_name') or 'Unknown'
        self.mastery_badge = self.replay_data.get(
            'battle_summary').get('mastery_badge') or 0
        self.battle_start_time = self.battle_summary.get(
            'battle_start_timestamp') or 'Unknown'

        if self.battle_result_num == 1:
            self.battle_result = 'Victory'
        elif self.battle_result_num == 0:
            self.battle_result = 'Defeat'
        else:
            self.battle_result = 'Draw'

        # Protagonist performance
        self.protagonist_id = self.battle_summary.get('protagonist')
        self.protagonist_name = self.replay_data.get(
            'players').get(str(self.protagonist_id)).get('nickname')
        self.players_data = self.replay_data.get('players')

    def image(self, bg=1, brand=1, darken=1, mapname=0, mastery=1, detailed_colors=1, hpbars=1):
        """
        bg - Draw background image \n
        brand - Draw branding \n
        darken - Draw dark bg overlay \n
        mapname - Draw map name and result \n
        """

        self.detailed_colors = detailed_colors
        self.hpbars = hpbars

        self.font_size = 16
        self.font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", self.font_size)
        self.font_fat = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_fat.ttf", (int(self.font_size * 1.25)))
        self.font_slim = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_slim.ttf", self.font_size)
        self.font_title = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", (self.font_size * 5))
        self.font_platoon = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_slim.ttf", 12)
        self.team_rating_font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", 18)
        self.bottom_stats_font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_fat.ttf", int(self.font_size))

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

        player_card_margin = 60
        self.text_margin_w = self.font_size
        self.text_margin_h = 5
        # Will bhe devided by 2
        self.platoon_icon_margin = self.text_margin_w + \
            ((28 - self.text_margin_w) * (self.room_type_mod))
        # Height of each player card
        self.image_step = 54
        self.map_name_margin = self.image_step * 2 * mapname

        mastery_badge_size = round(self.image_step * 1.5)
        self.mastery_badge_margin = (
            mastery_badge_size * 2 * mapname) + self.image_step

        # Width of each player card
        text_check = Image.new('RGBA', (0, 0), (0, 0, 0, 0))
        text_check = ImageDraw.Draw(text_check)

        self.all_players = []
        self.team_length_all = [0, 0]
        self.team_rating = [0, 0]
        self.longest_name = 0
        self.longest_stat = 0

        self.global_stat_max_width = {}
        self.global_stat_total_width = 0

        self.team_points = self.replay_data.get('team_points', {0: 0, 1: 0})
        self.best_rating = self.replay_data.get('best_rating', None)
        self.rating_descr = self.replay_data.get('rating_descr', None)
        self.players_data = sorted(
            self.players_data.values(), key=itemgetter('rating_value'), reverse=True)

        for player in self.players_data:
            self.all_players.append(player)

            full_name = f'{player.get("nickname")} [{player.get("clan_tag")}]'
            vehicle_name = f'{player.get("player_vehicle")}  '

            full_name_w, _ = text_check.textsize(
                full_name, self.font)
            vehicle_name_w, _ = text_check.textsize(
                vehicle_name, self.font)

            if full_name_w > self.longest_name:
                self.longest_name = full_name_w
            if vehicle_name_w > self.longest_name:
                self.longest_name = vehicle_name_w

            if player.get('team') == 2:
                self.team_rating[1] += player.get('rating_value')
                self.team_length_all[1] += 1
            else:
                self.team_rating[0] += player.get('rating_value')
                self.team_length_all[0] += 1

            for stat in self.stats:
                stat_font = self.get_font(None)
                stat_str = f'{player.get(stat)}'
                text_w, _ = text_check.textsize(stat_str, font=stat_font)
                max_width = self.global_stat_max_width.get(stat) or 0
                if text_w > max_width:
                    self.global_stat_max_width[stat] = text_w

        longest_stat, _ = text_check.textsize(
            f'{self.longest_stat}', self.font)

        if self.team_length_all[0] > self.team_length_all[1]:
            self.larger_team = self.team_length_all[0]
        else:
            self.larger_team = self.team_length_all[1]

        total_width = self.platoon_icon_margin
        for stat in self.stats:
            stat_value = str(self.best_rating.get(
                stat, self.players_data[0].get(stat)))
            text_w, _ = text_check.textsize(stat_value, font=stat_font)
            offset = (text_w + (self.text_margin_w))
            total_width += offset

        self.player_card_w = int(self.platoon_icon_margin + self.longest_name +
                                 (self.text_margin_w) + total_width)

        frame_w = (self.player_card_w * 2) + (player_card_margin * 3)
        frame_h = int((ceil((len(self.all_players) / 2) + 4))
                      * self.image_step) + self.map_name_margin + self.mastery_badge_margin

        frame = Image.new('RGBA', (frame_w, frame_h), (0, 0, 0, 0))
        self.image = frame
        self.image_w, self.image_h = frame.size
        self.draw_frame = ImageDraw.Draw(self.image)
        self.platoon_image = Image.open(
            './cogs/replays/render/icons/platoon.png')

        # Margin from frame border
        self.image_min_w = int((self.image_w - (self.player_card_w * 2)) / 3)
        self.image_min_h = int(
            (frame_h - (ceil((self.larger_team) + 2)) * self.image_step) / 2)

        self.enemy_team_offset_w = self.player_card_w + self.image_min_w

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

        if brand == 1:
            overlay_brand_wi = Image.open(
                './cogs/replays/render/wot_inspector.png')
            raw_brand_wi_w, raw_brand_wi_h = overlay_brand_wi.size
            brand_ratio = (self.image_step / 2) / raw_brand_wi_h
            overlay_brand_wi = overlay_brand_wi.resize(
                (int(raw_brand_wi_w * brand_ratio), int((raw_brand_wi_h * brand_ratio))))
            overlay_brand_wi_w, overlay_brand_wi_h = overlay_brand_wi.size

            wi_branding_h = self.text_margin_w
            wi_branding_w = frame_w - wi_branding_h - overlay_brand_wi_w
            self.image.paste(overlay_brand_wi, box=(
                wi_branding_w, wi_branding_h), mask=overlay_brand_wi.split()[3])

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

            self.image_min_h = int(result_text_h + self.image_step)

            battle_result_draw_w = int((self.image_w - result_text_w) / 2)
            battle_result_draw_h = int(
                (self.image_min_h - result_text_h) / 2)

            self.draw_frame.text((battle_result_draw_w, battle_result_draw_h), battle_result_str,
                                 fill=result_font_color, font=self.font_title)

        if mapname == 0 and mastery == 1 and self.mastery_badge > 0:
            # Draw Mastery badge
            mastery_badge_icon = Image.open(
                f'./cogs/replays/render/icons/mastery_badge_{self.mastery_badge}.png')
            mastery_badge_icon = mastery_badge_icon.resize(
                (mastery_badge_size, mastery_badge_size))

            self.image_min_h = self.mastery_badge_margin + self.image_step
            mastery_badge_icon_w = int((self.image_w - mastery_badge_size) / 2)
            mastery_badge_icon_h = int(
                (self.image_min_h - mastery_badge_size) / 2)

            self.image.paste(mastery_badge_icon, box=(
                mastery_badge_icon_w, mastery_badge_icon_h), mask=mastery_badge_icon.split()[3])

        step = [0, 0]
        for player in self.all_players:
            step[player.get('team') - 1] += 1

            team_offset_w = self.image_min_w
            if player.get('team') == 2:
                team_offset_w += self.enemy_team_offset_w

            player_card = self.draw_player_card(player)
            plate_w_pos = int(team_offset_w)
            plate_h_pos = int(self.image_min_h +
                              (self.image_step * step[player.get('team') - 1]))

            self.image.paste(player_card, box=(
                plate_w_pos, plate_h_pos), mask=player_card.split()[3])

        self.draw_ui_top()
        self.draw_ui_bot()

        error_rate = self.player_card_w - self.longest_name - \
            self.global_stat_total_width - self.platoon_icon_margin

        if error_rate < 0:
            raise Exception(
                'Negative error_rate detected. UI will not render correctly')

        final_buffer = BytesIO()
        self.image.save(final_buffer, 'png')
        final_buffer.seek(0)
        image_file = File(
            filename=f"result.png", fp=final_buffer)

        return image_file

    def draw_ui_bot(self):
        team_card_w = (self.player_card_w * 2) + self.image_min_w
        team_card_h = self.image_step - (self.text_margin_h * 2)
        icon_size = int(team_card_h / 2)

        # Draw bottom team card
        team_card_bot = Image.new(
            'RGBA', (team_card_w, (team_card_h)), (51, 51, 51, 255))
        bot_team_card_w, bot_team_card_h = team_card_bot.size
        bot_card_draw_w = self.image_min_w
        bot_card_draw_h = self.image_min_h + \
            (self.image_step * (ceil((self.larger_team) + 1)))

        # Draw bottom battle results
        draw_bot = ImageDraw.Draw(team_card_bot)

        # Get map name and battle result text sizes
        map_name_str = f'{self.map_name} {self.battle_type_str}'
        battle_result_str = f'{self.battle_result} {self.room_type_str}'
        map_name_w, map_name_h = draw_bot.textsize(
            map_name_str, font=self.font)
        battle_result_w, battle_result_h = draw_bot.textsize(
            battle_result_str, font=self.font)

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

        draw_bot.text((battle_result_draw_w, battle_result_draw_h), battle_result_str,
                      self.font_color_base, font=self.font)
        draw_bot.text((map_name_draw_w, map_name_draw_h), map_name_str,
                      self.font_color_base, font=self.font)

        protagonist_card_unique = Image.new(
            'RGBA', (self.player_card_w, (self.image_step - 10)), (0, 0, 0, 0))
        protagonist_card_w, protagonist_card_h = protagonist_card_unique.size
        draw_bot_pr_card = ImageDraw.Draw(protagonist_card_unique)

        last_icon_pos = 0
        for icon in self.stats_bottom:
            icon_name = icon
            icon_value = self.battle_summary.get(icon_name)
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
            icon_draw_h = int((protagonist_card_h - icon_h) / 2)

            stat_text_draw_w = icon_draw_w + icon_w + (icon_w / 4)
            stat_text_draw_h = int((protagonist_card_h - stat_text_h) / 2)

            protagonist_card_unique.paste(icon, box=(
                icon_draw_w, icon_draw_h), mask=icon.split()[3])
            draw_bot_pr_card.text((stat_text_draw_w, stat_text_draw_h), stat_value,
                                  self.font_color_base, font=self.bottom_stats_font)

            last_icon_pos += icon_budle_width + icon_w

        # Add bottom card to UI
        protagonist_card_draw_w = int(
            (bot_team_card_w - (last_icon_pos - icon_size)) / 2)
        protagonist_card_draw_h = 0

        team_card_bot.paste(protagonist_card_unique, box=(
            protagonist_card_draw_w, protagonist_card_draw_h), mask=protagonist_card_unique.split()[3])

        self.image.paste(team_card_bot, box=(
            bot_card_draw_w, bot_card_draw_h), mask=team_card_bot.split()[3])

        # Draw icon key
        icon_key_card = Image.new(
            'RGBA', (self.image_w, (self.image_step)), (51, 51, 51, 0))
        draw_icon_key = ImageDraw.Draw(icon_key_card)
        icon_key_card_w, icon_key_card_h = icon_key_card.size

        # Draw a name for each icon
        last_key_icon_pos = 0
        for icon in self.stats:
            key_icon_size = int(icon_key_card_h / 2)
            try:
                key_icon = Image.open(
                    f'./cogs/replays/render/icons/{icon}.png')
            except:
                key_icon = Image.open(
                    './cogs/replays/render/icons/default_icon.png')
            key_icon = key_icon.resize((key_icon_size, key_icon_size))

            key_icon_descr_str = self.rating_descr.get(
                f'{icon}_descr', 'Unknown')
            key_icon_descr_w, key_icon_descr_h = draw_bot.textsize(
                key_icon_descr_str, font=self.bottom_stats_font)

            key_icon_draw_w = last_key_icon_pos
            key_icon_draw_h = int((icon_key_card_h - key_icon_size) / 2)
            icon_key_card.paste(key_icon, box=(
                key_icon_draw_w, key_icon_draw_h), mask=key_icon.split()[3])

            key_descr_draw_w = key_icon_draw_w + icon_size + self.text_margin_w
            key_descr_draw_h = int((icon_key_card_h - key_icon_descr_h) / 2)
            draw_icon_key.text((key_descr_draw_w, key_descr_draw_h), key_icon_descr_str,
                               self.font_color_base, font=self.bottom_stats_font)

            key_icon_budle_width = key_icon_size + key_icon_descr_w
            last_key_icon_pos += key_icon_budle_width + key_icon_size

        # Paste card to frame
        icon_key_card_draw_w = int(
            (icon_key_card_w - (last_key_icon_pos - key_icon_size)) / 2)
        icon_key_card_draw_h = self.image_h - self.image_step
        self.image.paste(icon_key_card, box=(
            icon_key_card_draw_w, icon_key_card_draw_h), mask=icon_key_card.split()[3])

        return

    def draw_ui_top(self):
        team_card_w = (self.player_card_w * 2) + self.image_min_w
        team_card_h = self.image_step - (self.text_margin_h * 2)

        # Draw top team card bg
        team_card_top = Image.new(
            'RGBA', (team_card_w, (team_card_h)), (51, 51, 51, 255))
        team_card_w, team_card_h = team_card_top.size
        top_card_draw_w = self.image_min_w
        top_card_draw_h = self.image_min_h
        self.image.paste(team_card_top, box=(
            top_card_draw_w, top_card_draw_h), mask=team_card_top.split()[3])

        for team in [0, 1]:
            team_rating = self.team_rating[team]

            team_offs = self.image_min_w + \
                (self.enemy_team_offset_w * team)

            card_height = self.image_step - (self.text_margin_h * 2)
            card_width = self.player_card_w

            team_card = Image.new(
                'RGBA', (card_width, (card_height)), (0, 0, 0, 0))
            team_card_w, team_card_h = team_card.size
            team_card_draw = ImageDraw.Draw(team_card)

            icon_frame_w = icon_frame_h = int(
                (card_height * 2 / 3) - self.text_margin_h)

            player_list = Image.open(
                f'./cogs/replays/render/icons/player_list.png')
            player_list = player_list.resize((icon_frame_w, icon_frame_h))
            player_list_w, player_list_h = player_list.size

            card_draw_w = team_offs
            card_draw_h = self.image_min_h

            player_list_draw_w = self.platoon_icon_margin
            icons_draw_h = int((team_card_h - player_list_h) / 2)

            # Draw Team points if battle type is Supremacy
            if self.battle_type == 1:
                team_points = f'Points: ~{self.team_points.get(team)}'
                points_w, points_h = team_card_draw.textsize(
                    team_points, font=self.bottom_stats_font)
                points_draw_w = player_list_draw_w + player_list_w + self.text_margin_w
                points_draw_h = int((team_card_h - points_h) / 2)
                team_card_draw.text((points_draw_w, points_draw_h), team_points,
                                    self.font_color_base, font=self.bottom_stats_font)

            team_card.paste(player_list, box=(
                player_list_draw_w, icons_draw_h), mask=player_list.split()[3])

            last_stat_pos = 0
            for icon in self.stats_reversed:
                icon_name = icon
                try:
                    icon = Image.open(
                        f'./cogs/replays/render/icons/{icon_name}.png')
                except:
                    icon = Image.open(
                        './cogs/replays/render/icons/default_icon.png')
                icon = icon.resize((icon_frame_w, icon_frame_h))
                icon_w, icon_h = icon.size
                max_width = self.global_stat_max_width.get(
                    icon_name, self.global_stat_max_width.get('damage_made'))

                draw_w = int(
                    ((team_card_w - self.text_margin_w - max_width - last_stat_pos) + ((max_width - icon_w) / 2)))
                # draw_w = int(team_card_w)

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
        rating = player.get('rating') or 0
        rating_value = player.get('rating_value') or 0
        survived = player.get('survived') or 0
        hero_bonus_exp = player.get('hero_bonus_exp') or 0
        damage = player.get('damage') or 0
        kills = player.get('kills') or 0
        platoon = player.get('platoon_str') or 0
        team = player.get('team') or 0
        nickname = player.get('nickname') or 0
        player_wr = player.get('player_wr') or 0
        clan = player.get("clan_tag") or 0
        vehicle = player.get('player_vehicle') or 0
        vehicle_battles = player.get('vehicle_battles') or 0
        vehicle_wr = player.get('vehicle_wr') or 0
        damage_recieved = player.get(
            'performance').get('damage_received') or 1
        hp_left = player.get('performance').get('hitpoints_left') or 0
        total_hp = hp_left + damage_recieved
        hp_percent = round((hp_left / total_hp), 2)

        clan_tag = ''
        if clan:
            clan_tag = f'[{clan}]'

        # Draw name bg plates
        player_card = Image.new(
            'RGBA', (self.player_card_w, (self.image_step - 10)), self.player_card_color)
        player_card_w, player_card_h = player_card.size

        draw = ImageDraw.Draw(player_card)

        # Draw HP Bars
        hp_bar_w = 3 * self.hpbars
        if self.hpbars == 1:
            hp_bar_base_color = (100, 100, 100, 200)
            if team == 1:
                hp_bar_color = (123, 219, 101, 200)
            else:
                hp_bar_color = (219, 109, 101, 200)

            hp_bar_base_h = int((self.font_size * 2))
            hp_bar_h = int(hp_percent * hp_bar_base_h)

            # Draw HP bars bg
            hp_bars_base_draw_w1 = self.platoon_icon_margin
            hp_bars_base_draw_h1 = self.text_margin_h
            hp_bars_base_draw_w2 = hp_bars_base_draw_w1 + hp_bar_w
            hp_bars_base_draw_h2 = hp_bars_base_draw_h1 + hp_bar_base_h + 1
            draw.rectangle([(hp_bars_base_draw_w1, hp_bars_base_draw_h1),
                            (hp_bars_base_draw_w2, hp_bars_base_draw_h2)], fill=hp_bar_base_color)

            if survived:
                hp_bars_draw_h1 = hp_bars_base_draw_h2 - hp_bar_h
                hp_bars_draw_h2 = hp_bars_base_draw_h2
                draw.rectangle([(hp_bars_base_draw_w1, hp_bars_draw_h1),
                                (hp_bars_base_draw_w2, hp_bars_draw_h2)], fill=hp_bar_color)

        # Draw platoons
        if platoon and self.room_type_mod == 1:
            platoon_font = self.font_platoon
            platoon_font_color = self.font_color_base
            platoon_img = self.platoon_image.copy()
            draw_platoon = ImageDraw.Draw(platoon_img)

            platoon_str = f'{platoon}'
            text_w, text_h = draw.textsize(platoon_str, font=platoon_font)
            platoon_img_w, platoon_img_h = self.platoon_image.size

            draw_w = int((platoon_img_w - text_w) / 2)
            draw_h = 0
            draw_platoon.text((draw_w, draw_h), platoon_str,
                              platoon_font_color, font=platoon_font)

            platoon_w_pos = int(
                (self.platoon_icon_margin - platoon_img_w) / 2)
            platoon_h_pos = int((player_card_h - platoon_img_h) / 2)
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

        clan_str = f'{clan_tag}'
        tank_str = f'{vehicle}'
        name_str = f'{nickname}'
        tank_text_w, tank_text_h = draw.textsize(tank_str, font=tank_font)
        name_text_w, name_text_h = draw.textsize(name_str, font=name_font)
        clan_text_w, clan_text_h = draw.textsize(clan_str, font=name_font)

        draw_w = self.platoon_icon_margin
        tank_draw_w = int(self.platoon_icon_margin + (hp_bar_w * 3))
        tank_draw_h = self.text_margin_h
        name_draw_w = int(self.platoon_icon_margin + (hp_bar_w * 3))
        name_draw_h = int(
            player_card_h - name_text_h - self.text_margin_h)
        clan_draw_w = int(name_draw_w + name_text_w + (self.font_size / 2))
        clan_draw_h = name_draw_h

        draw.text((tank_draw_w, tank_draw_h), tank_str,
                  font_color_info, font=tank_font)
        draw.text((name_draw_w, name_draw_h), name_str,
                  font_color_name, font=name_font)
        draw.text((clan_draw_w, clan_draw_h), clan_str,
                  font_color_info, font=name_font)

        if hero_bonus_exp and hero_bonus_exp > 0:
            hero_icon = Image.open(
                f'./cogs/replays/render/icons/hero_icon.png')
            hero_icon = hero_icon.resize((self.font_size, self.font_size))
            hero_icon_w = int(
                tank_draw_w + (self.font_size / 2) + tank_text_w)
            hero_icon_h = self.text_margin_h + 1

            player_card.paste(hero_icon, box=(
                hero_icon_w, hero_icon_h), mask=hero_icon.split()[3])

        # Render performance stats
        last_stat_pos = 0
        for stat in self.stats_reversed:
            stat_value_raw = player.get(stat, -1)

            stat_value = stat_value_raw
            if not stat_value_raw.isnumeric():
                # stat_value = self.convert_to_num.sub('', stat_value_raw)
                stat_value = player.get(f'{stat}_value', -1)

            stat_max_width = self.global_stat_max_width.get(
                stat, 0)
            stat_str = f'{stat_value_raw}'

            stat_font = self.get_font(f'{stat}')
            stat_font_color = self.get_font(f'{stat}', 'color')
            if not survived:
                stat_font_color = font_color_info

            stat_text_w, stat_text_h = draw.textsize(
                stat_str, font=stat_font)

            stat_draw_w = int(
                ((player_card_w - self.text_margin_w - stat_max_width - last_stat_pos) + ((stat_max_width - stat_text_w) / 2)))
            stat_draw_h = int((player_card_h - stat_text_h) / 2)
            draw.text((stat_draw_w, stat_draw_h), stat_str,
                      stat_font_color, font=stat_font)

            # if stat == 'rating':
            if 'rating' in stat and self.best_rating.get(stat) and float(player.get(stat)) > 0 and self.detailed_colors == 1:
                best_value = self.best_rating.get(stat)

                best_value_w, _ = draw.textsize(
                    str(best_value), font=stat_font)
                stat_str_w, _ = draw.textsize(
                    stat_str, font=stat_font)

                rating_percent = float(stat_value) / best_value * 100
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

                rating_box_w1 = int(
                    player_card_w - self.text_margin_w - (best_value_w) - last_stat_pos - 1)
                rating_box_h1 = stat_draw_h + stat_text_h + 3
                rating_box_w2 = rating_box_w1 + best_value_w + 1
                rating_box_h2 = rating_box_h1 + 2

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

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
