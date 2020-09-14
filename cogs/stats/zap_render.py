from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageFilter

from discord import File
from io import BytesIO

import requests

from datetime import datetime, timedelta
from pytz import timezone

class Render:
    def __init__(self, player_id: int, realm: str, bg_url: str, data: dict):
        self.tank_count = len(data.get('session').get('vehicles'))
        if len(data.get('session').get('vehicles')) > 10:
            self.tank_count = 10
        self.render_prep(bg_url)
        self.render_header(player_details=data.get("player_details"))
        self.render_all_stats(player_data=data)
        self.session_timestamp = data.get('session').get('timestamp')

        # Render a card for each tank in detailed stats
        for i, tank_session in enumerate(data.get('session').get('vehicles')):
            if i > 10:
                break
            last_session = data.get('last_session').get('vehicles').get(str(tank_session.get("tank_id"))).get('all')
            self.render_detailed_stats(tank_data=tank_session, last_tank_data=last_session, card_index=i)

    def render_prep(self, bg_url: str):
        # Import fonts
        self.font_size = 32
        self.font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", self.font_size)
        self.font_half_size = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", int(self.font_size / 1.5))
        self.font_bold = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_fat.ttf", self.font_size)
        self.font_slim = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_slim.ttf", int(self.font_size * 0.9))

        self.font_color_base = (255, 255, 255)
        self.font_color_card = (0, 0, 0, 100)
        self.font_color_none = (255, 255, 255, 0)
        self.font_color_none = (0, 0, 0, 0)
        self.font_color_half = (200, 200, 200, 100)
        self.font_color_session_time = (200, 200, 200, 255)

        self.tank_tier_dict = {
            0: "",
            1: "I",
            2: "II",
            3: "III",
            4: "IV",
            5: "V",
            6: "VI",
            7: "VII",
            8: "VIII",
            9: "IX",
            10: "X",
        }

        self.frame_margin_w = 50
        self.frame_margin_h = 100
        self.header_h = 150
        self.text_margin_w = 30
        self.text_margin_h = 20
        self.card_margin_h = int(self.frame_margin_h / 4)
        self.base_card_w = 900
        self.base_card_h = 200
        self.detailed_card_h = int(self.base_card_h / 1.5)
        self.frame_w = self.base_card_w + (self.frame_margin_w * 2)
        self.frame_h = int((self.frame_margin_h - self.card_margin_h) + ((self.header_h + self.base_card_h) + (self.card_margin_h * 2)) +
                           (self.tank_count * (self.detailed_card_h + self.card_margin_h)))

        # Fill background with a non-transparent layer to fix self.frame transparency due to RGBA
        solid_bg = Image.new(
            'RGB', (self.frame_w, self.frame_h), (0, 0, 0))

        if bg_url:
            # Get image from URL
            response = requests.get(bg_url)
            try:
                bg_image = Image.open(BytesIO(response.content))
            except:
                print("Failed to load custom bg image")
                bg_image = Image.open('./cogs/replays/render/bg_frame.png')
        else:
            bg_image = Image.open('./cogs/replays/render/bg_frame.png')

        try:
            bg_image_w, bg_image_h = bg_image.size
            bg_image_ratio = self.frame_h / bg_image_h
            if bg_image_ratio < self.frame_w / bg_image_w:
                bg_image_ratio = self.frame_w / bg_image_w
            bg_image = bg_image.resize(
                (int(bg_image_w * bg_image_ratio), int(bg_image_h * bg_image_ratio)))

            blur_radius = 10
            bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

            new_bg_w, new_bg_h = bg_image.size
            centering_shift_w =  - int(((new_bg_w - self.frame_w) / 2))
            centering_shift_h = -int(((new_bg_h - self.frame_h) / 2))
            
            solid_bg.paste(bg_image, box=(
                centering_shift_w, centering_shift_h))
        except Exception as e:
            print(e)
            print("Failed to render bg image")
            
        self.frame = solid_bg

        # # Draw session start time
        # frame_draw = ImageDraw.Draw(self.frame)
        # time_text_w, time_text_h = frame_draw.textsize(
        #     self.session_timestamp, font=self.font_slim)
        # time_draw_w = int((self.frame_w - time_text_w) / 2)
        # time_draw_h = int(((self.frame_margin_h / 2) - time_text_h) / 2)
        # frame_draw.text((time_draw_w, time_draw_h), self.session_timestamp,
        #                 self.font_color_session_time, font=self.font_slim)

    def get_rating_col(self, rating: int):
        color_dict = {
            0: (0, 0, 0, 100),          # Matching BG
            300: (251, 83, 83, 255),    # Red
            450: (255, 160, 49, 255),   # Orange yellow
            650: (255, 244, 65, 255),   # Yellow
            900: (149, 245, 62, 255),   # Lime green
            1200: (103, 190, 51, 255),  # Dark green
            1600: (106, 236, 255, 255), # Teal
            2000: (46, 174, 193, 255),  # Blue
            2450: (208, 108, 255, 255), # Pink
            2900: (142, 65, 177, 255)   # Magenta
        }

        for k in color_dict.keys():
            d = k - rating
            if d <= 0:
                color = color_dict.get(k)
            else:
                break

        return color

    def render_header(self, player_details: dict):
        header_w = self.base_card_w
        header_h = self.header_h
        header_card = Image.new(
            'RGBA', (header_w, header_h), self.font_color_card)
        header_draw = ImageDraw.Draw(header_card)

        nickanme = player_details.get('nickname')
        clan_tag = player_details.get('clan', {}).get('tag')
        clan_tag_str = ''
        if clan_tag:
            clan_tag_str = f'[{clan_tag}]'
        name_clan_str = f"{nickanme} {clan_tag_str}"
        battles_type = 'Random Battles'

        # Text size
        name_clan_w, _ = header_draw.textsize(
            name_clan_str, font=self.font_bold)
        b_type_w, _ = header_draw.textsize(
            battles_type, font=self.font)

        # Draw battle type
        draw_b_type_w = int((header_w - b_type_w) / 2)
        draw_b_type_h = int((self.text_margin_h * 2))
        header_draw.text((draw_b_type_w, draw_b_type_h), battles_type,
                         self.font_color_base, font=self.font)
        # Draw player name and tag
        draw_name_w = int((header_w - name_clan_w) / 2)
        draw_name_h = int((self.text_margin_h * 2)) + draw_b_type_h
        header_draw.text((draw_name_w, draw_name_h), name_clan_str,
                         self.font_color_base, font=self.font_bold)

        # Render card on frame
        self.frame.paste(header_card, box=(
            self.frame_margin_w, int(self.frame_margin_h / 2)), mask=header_card.split()[3])

    def render_all_stats(self, player_data: dict):
        stats_all_w = self.base_card_w
        stats_all_h = self.base_card_h
        stats_all_card = Image.new(
            'RGBA', (stats_all_w, stats_all_h), self.font_color_card )
        stats_draw = ImageDraw.Draw(stats_all_card)

        # Organize Data
        player_details = player_data.get("player_details")
        live_stats_random = player_details.get('statistics', {}).get('all', {})
        session_stats_random = player_data.get('session', {}).get('stats_random', {})
        
        player_wn8 = player_details.get('career_wn8', '-')
        if player_wn8 != '-':
            player_wn8_color = self.get_rating_col(player_wn8)

        # Session Stats
        session_battles = session_stats_random.get('battles')
        session_dmg_all = session_stats_random.get('damage_dealt')
        session_wins_all = session_stats_random.get('wins')
        session_dmg_avg = f"{round(session_dmg_all / session_battles)}"
        session_wr_avg = f"{round(((session_wins_all / session_battles) * 100), 2)}% ({session_battles})"
        # Calculate WN8
        session_wn8 = player_data.get('session').get('session_wn8', '-')
        session_wn8_color = self.get_rating_col(session_wn8)

        # Live stats
        live_battles = live_stats_random.get('battles')
        live_dmg_all = live_stats_random.get('damage_dealt')
        live_wins_all = live_stats_random.get('wins')

        old_battles = live_battles - session_battles
        old_dmg_all = live_dmg_all - session_dmg_all
        old_wins = live_wins_all - session_wins_all

        wr_change = round((((live_wins_all / live_battles) * 100) - ((old_wins / old_battles) * 100)), 2)
        if wr_change == 0:
            wr_change_str = f""
        elif wr_change > 0:
            wr_change_str = f" (+{wr_change}%)"
        else:
            wr_change_str = f" ({wr_change}%)"

        dmg_change = round(((live_dmg_all / live_battles) - (old_dmg_all / old_battles)))
        if dmg_change == 0:
            dmg_change_str = f""
        elif dmg_change > 0:
            dmg_change_str = f" (+{dmg_change})"
        else:
            dmg_change_str = f" ({dmg_change})"

        live_dmg_avg = f"{round(live_dmg_all / live_battles)} {dmg_change_str}"
        live_wr_avg = f"{round(((live_wins_all / live_battles) * 100), 2)}%{wr_change_str}"

        # Calculate WN8
        live_wn8 = str(player_wn8)

        # Get text size
        damage_text_w, _ = stats_draw.textsize(
            'Damage', font=self.font)
        winrate_text_w, _ = stats_draw.textsize(
            'Winrate', font=self.font)
        wn8_text_w, wn8_text_h = stats_draw.textsize(
            'WN8', font=self.font_bold)
        # Session Stats
        session_dmg_w, _ = stats_draw.textsize(
            session_dmg_avg, font=self.font)
        session_wn8_w, _ = stats_draw.textsize(
            str(session_wn8), font=self.font_bold)
        session_wr_w, _ = stats_draw.textsize(
            session_wr_avg, font=self.font)
        # Live stats
        live_dmg_w, _ = stats_draw.textsize(
            live_dmg_avg, font=self.font)
        live_wn8_w, _ = stats_draw.textsize(
            live_wn8, font=self.font_bold)
        live_wr_w, _ = stats_draw.textsize(
            live_wr_avg, font=self.font)

        # Margins
        stats_margin_w = int((stats_all_w - (4 * self.text_margin_w)) / 3)
        all_text_h = int((wn8_text_h * 3) + (self.text_margin_h * 2))
        top_bot_margin = int((self.base_card_h - all_text_h) / 2)
        row_step = int(wn8_text_h + self.text_margin_h)

        # Top row
        # Draw damage
        draw_damage_w = int((2 * self.text_margin_w) +
                            ((stats_margin_w - damage_text_w) / 2))
        draw_damage_h = top_bot_margin
        stats_draw.text((draw_damage_w, draw_damage_h), 'Damage',
                        self.font_color_base, font=self.font)
        # Draw WN8
        draw_wn8_name_w = int((2 * self.text_margin_w) + stats_margin_w +
                              ((stats_margin_w - wn8_text_w) / 2))
        draw_wn8_name_h = top_bot_margin
        stats_draw.text((draw_wn8_name_w, draw_wn8_name_h), 'WN8',
                        self.font_color_base, font=self.font)
        # Draw winrate
        draw_winrate_w = int((2 * self.text_margin_w) + (stats_margin_w * 2) +
                             ((stats_margin_w - winrate_text_w) / 2))
        draw_winrate_h = top_bot_margin
        stats_draw.text((draw_winrate_w, draw_winrate_h), 'Winrate',
                        self.font_color_base, font=self.font)

        # Middle row
        # Draw damage
        draw_dmg_w = int((2 * self.text_margin_w) +
                         ((stats_margin_w - session_dmg_w) / 2))
        draw_dmg_h = top_bot_margin + row_step
        stats_draw.text((draw_dmg_w, draw_dmg_h), session_dmg_avg,
                        self.font_color_base, font=self.font)
        # Draw WN8
        draw_wn8_w = int((2 * self.text_margin_w) + stats_margin_w +
                         ((stats_margin_w - session_wn8_w) / 2))
        draw_wn8_h = top_bot_margin + row_step
        stats_draw.text((draw_wn8_w, draw_wn8_h), str(session_wn8),
                        self.font_color_base, font=self.font_bold)
        # Draw WN8 color bar
        if type(session_wn8) == int:
            wn8_box_w1 = draw_wn8_w - 16
            wn8_h1 = draw_wn8_h + 2
            wn8_w2 = wn8_box_w1 + 10
            wn8_h2 = wn8_h1 + self.font_size
            stats_draw.rectangle([(wn8_box_w1, wn8_h1),
                                  (wn8_w2, wn8_h2)], fill=session_wn8_color)
        # Draw winrate
        draw_wr_w = int((2 * self.text_margin_w) + (stats_margin_w * 2) +
                        ((stats_margin_w - session_wr_w) / 2))
        draw_wr_h = top_bot_margin + row_step
        stats_draw.text((draw_wr_w, draw_wr_h), session_wr_avg,
                        self.font_color_base, font=self.font)

        # Bottom row
        # Draw damage
        draw_live_dmg_w = int((self.text_margin_w * 2) +
                              ((stats_margin_w - live_dmg_w) / 2))
        draw_live_dmg_h = top_bot_margin + (2 * row_step)
        stats_draw.text((draw_live_dmg_w, draw_live_dmg_h), live_dmg_avg,
                        self.font_color_base, font=self.font)
        # Draw WN8
        draw_live_wn8_w = int((2 * self.text_margin_w) + stats_margin_w +
                              ((stats_margin_w - live_wn8_w) / 2))
        draw_live_wn8_h = top_bot_margin + (2 * row_step)
        stats_draw.text((draw_live_wn8_w, draw_live_wn8_h), live_wn8,
                        self.font_color_base, font=self.font_bold)
        # Draw WN8 color bar
        if type(player_wn8) == int:
            cwn8_box_w1 = draw_live_wn8_w - 16
            cwn8_h1 = draw_live_wn8_h + 2
            cwn8_w2 = cwn8_box_w1 + 10
            cwn8_h2 = cwn8_h1 + self.font_size
            stats_draw.rectangle([(cwn8_box_w1, cwn8_h1),
                                  (cwn8_w2, cwn8_h2)], fill=player_wn8_color)
        # Draw winrate
        draw_live_wr_w = int((2 * self.text_margin_w) + (stats_margin_w * 2) +
                             ((stats_margin_w - live_wr_w) / 2))
        draw_live_wr_h = top_bot_margin + (2 * row_step)
        stats_draw.text((draw_live_wr_w, draw_live_wr_h), live_wr_avg,
                        self.font_color_base, font=self.font)

        # Render card on frame
        stats_all_render_h = int(
            (self.frame_margin_h / 2) + (self.header_h) + self.card_margin_h)
        self.frame.paste(stats_all_card, box=(
            self.frame_margin_w, stats_all_render_h), mask=stats_all_card.split()[3])

    def render_detailed_stats(self, tank_data: dict, last_tank_data: dict, card_index):
        stats_detailed_w = self.base_card_w
        stats_detailed_h = self.detailed_card_h
        stats_detailed_card = Image.new(
            'RGBA', (stats_detailed_w, stats_detailed_h), self.font_color_card)
        stats_draw = ImageDraw.Draw(stats_detailed_card)

        # Organize tank data
        tank_stats = tank_data.get('all')
        tank_tier_int = tank_data.get('tank_tier')
        tank_tier = self.tank_tier_dict.get(tank_tier_int)
        tank_name = f"{tank_data.get('tank_name')}"
        tank_battles = tank_stats.get("battles")
        # Performance
        tank_wr_value = round(((tank_stats.get('wins') / tank_battles) * 100))
        tank_wr = f"WR: {tank_wr_value}% ({tank_battles})"
        tank_dmg_value = round((tank_stats.get('damage_dealt') / tank_battles))
        tank_dmg = f"DMG: {tank_dmg_value}"
        tank_xp_value = round((tank_stats.get('xp') / tank_battles))
        tank_xp = f"XP: {tank_xp_value}"
        tank_wn8_value = tank_data.get('tank_wn8', '')
        # Extra spaces to fit the color bar
        tank_wn8 = f"{tank_wn8_value}"
        if tank_wn8_value != '':
            tank_wn8_color = self.get_rating_col(tank_wn8_value)
        else:
            tank_wn8_color = (0, 0, 0, 100)
        # Previous session stats
        # Will be None when last session not available
        last_session_bool = last_tank_data.get("battles") > 0
        if last_session_bool:
            last_battles = last_tank_data.get('battles')
            last_wr_value = round(
                ((last_tank_data.get('wins') / last_battles) * 100))
            last_dmg_value = round(
                (last_tank_data.get('damage_dealt') / last_battles))
            last_xp_value = round(
                (last_tank_data.get('xp') / last_battles))

        # Get text size
        tier_text_w, tier_text_h = stats_draw.textsize(
            tank_tier, font=self.font_half_size)
        max_tier_text_w, _ = stats_draw.textsize(
            "X", font=self.font_half_size)
        _, name_text_h = stats_draw.textsize(
            tank_name, font=self.font_bold)
        wr_text_w, wr_text_h = stats_draw.textsize(
            tank_wr, font=self.font)
        xp_text_w, _ = stats_draw.textsize(
            tank_xp, font=self.font)
        dmg_text_w, dmg_text_h = stats_draw.textsize(
            tank_dmg, font=self.font)
        wn8_text_w, _ = stats_draw.textsize(
            tank_wn8, font=self.font_bold)

        # Margins
        text_w_margin = self.text_margin_w * 2
        text_h_margin = int((stats_detailed_h - (name_text_h + wr_text_h)) / 3)
        bottom_metrics_text_w = (dmg_text_w + int(dmg_text_h)) + (
            xp_text_w + int(dmg_text_h)) + (wr_text_w + int(dmg_text_h)) + (self.text_margin_w * 8)
        bottom_metric_margin = int(
            (bottom_metrics_text_w) / 3)
        bottom_metrics_min_margin = int(
            (stats_detailed_w - bottom_metrics_text_w) / 2)

        # Top row
        # Draw tank name
        draw_name_w = text_w_margin + max_tier_text_w
        draw_name_h = text_h_margin
        stats_draw.text((draw_name_w, draw_name_h), tank_name,
                        self.font_color_base, font=self.font_bold)
        # Draw tank tier
        # Color premium vehicles
        tier_color = self.font_color_base
        draw_tier_w = draw_name_w - tier_text_w - int(self.font_size / 3)
        draw_tier_h = text_h_margin + int((name_text_h - tier_text_h) / 2)
        stats_draw.text((draw_tier_w, draw_tier_h), tank_tier,
                        tier_color, font=self.font_half_size)
        # Draw tank WN8
        draw_wn8_w = int((stats_detailed_w - wn8_text_w - text_w_margin))
        draw_wn8_h = draw_name_h
        stats_draw.text((draw_wn8_w, draw_wn8_h), tank_wn8,
                        self.font_color_base, font=self.font_bold)
        # Draw WN8 color bar
        wn8_box_w1 = draw_wn8_w - 16
        wn8_h1 = draw_wn8_h + 2
        wn8_w2 = wn8_box_w1 + 10
        wn8_h2 = wn8_h1 + self.font_size
        stats_draw.rectangle([(wn8_box_w1, wn8_h1),
                              (wn8_w2, wn8_h2)], fill=tank_wn8_color)
        # Bottom row
        # Draw tank damage
        draw_dmg_w = int(
            (bottom_metric_margin - dmg_text_w) / 2) + bottom_metrics_min_margin + int(dmg_text_h / 2)
        draw_dmg_h = int(stats_detailed_h - dmg_text_h - text_h_margin)
        stats_draw.text((draw_dmg_w, draw_dmg_h), tank_dmg,
                        self.font_color_base, font=self.font)
        if last_session_bool and tank_dmg_value != last_dmg_value:
            # Draw progress arrow
            arrow_size = int(dmg_text_h / 2)
            pos_w = draw_dmg_w - int(arrow_size * 1.5)
            pos_h = draw_dmg_h + int((dmg_text_h - arrow_size) / 1.5)
            self.draw_progress_arrow(
                draw=stats_draw, pos_w=pos_w, pos_h=pos_h, size=arrow_size, isup=(tank_dmg_value > last_dmg_value))

        # Draw tank xp
        draw_xp_w = int((bottom_metric_margin * 1) +
                        ((bottom_metric_margin - xp_text_w) / 2)) + bottom_metrics_min_margin + int(dmg_text_h / 2)
        draw_xp_h = draw_dmg_h
        stats_draw.text((draw_xp_w, draw_xp_h), tank_xp,
                        self.font_color_base, font=self.font)
        if last_session_bool and tank_xp_value != last_xp_value:
            # Draw progress arrow
            arrow_size = int(dmg_text_h / 2)
            pos_w = draw_xp_w - int(arrow_size * 1.5)
            pos_h = draw_xp_h + int((dmg_text_h - arrow_size) / 1.5)
            self.draw_progress_arrow(
                draw=stats_draw, pos_w=pos_w, pos_h=pos_h, size=arrow_size, isup=(tank_xp_value > last_xp_value))

        # Draw tank winrate
        draw_wr_w = int((bottom_metric_margin * 2) +
                        ((bottom_metric_margin - wr_text_w) / 2)) + bottom_metrics_min_margin + int(dmg_text_h / 2)
        draw_wr_h = draw_dmg_h
        stats_draw.text((draw_wr_w, draw_wr_h), tank_wr,
                        self.font_color_base, font=self.font)
        if last_session_bool and tank_wr_value != last_wr_value:
            # Draw progress arrow
            arrow_size = int(dmg_text_h / 2)
            pos_w = draw_wr_w - int(arrow_size * 1.5)
            pos_h = draw_wr_h + int((dmg_text_h - arrow_size) / 1.5)
            self.draw_progress_arrow(
                draw=stats_draw, pos_w=pos_w, pos_h=pos_h, size=arrow_size, isup=(tank_wr_value > last_wr_value))

        # Render card on frame
        stats_detailed_render_h = int(
            (self.frame_margin_h / 2) + ((2 * self.card_margin_h) + (self.base_card_h + self.header_h)) + (card_index * (stats_detailed_h + self.card_margin_h)))
        self.frame.paste(stats_detailed_card, box=(
            self.frame_margin_w, stats_detailed_render_h), mask=stats_detailed_card.split()[3])

    def draw_progress_arrow(self, draw, pos_w: int, pos_h: int, size: int, isup: bool):
        if isup:
            base_1_w = pos_w
            base_1_h = pos_h + size
            base_2_w = base_1_w + size
            base_2_h = base_1_h
            peak_w = pos_w + int(size / 2)
            peak_h = pos_h
            draw.polygon([(base_1_w, base_1_h), (base_2_w, base_2_h),
                          (peak_w, peak_h)], fill=(0, 255, 0, 100))
            return
        else:
            base_1_w = pos_w
            base_1_h = pos_h
            base_2_w = base_1_w + size
            base_2_h = base_1_h
            peak_w = pos_w + int(size / 2)
            peak_h = pos_h + size
            draw.polygon([(base_1_w, base_1_h), (base_2_w, base_2_h),
                          (peak_w, peak_h)], fill=(255, 0, 0, 100))

    def render_image(self):
        final_buffer = BytesIO()
        self.frame.save(final_buffer, 'png')
        final_buffer.seek(0)
        image_file = File(
            filename=f"result.png", fp=final_buffer)
        return image_file
