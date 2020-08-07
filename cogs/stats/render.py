from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageFilter

from discord import File
from io import BytesIO

import requests
import rapidjson

from cogs.api.mongoApi import StatsApi

from datetime import datetime, timedelta
# from cogs.api.mongoApi import StatsApi

Stats = StatsApi()


class Render:
    def __init__(self, player_id):
        player_details, last_stats_all, session_all, session_detailed = Stats.get_session_stats(
            player_id=player_id, session_duration=(datetime.utcnow() - timedelta(hours=24)))

        self.tank_count = len(session_detailed)
        self.render_prep()
        self.render_header(player_details=player_details)
        self.render_all_stats(stats_all=session_all,
                              last_stats_all=last_stats_all)
        # Render a card for each tank in detailed stats
        for i, tank_id in enumerate(list(session_detailed)):
            tank_stats = session_detailed.get(tank_id)
            self.render_detailed_stats(tank_stats=tank_stats, card_index=i)

        self.frame.show()

    def render_prep(self):
        # Import fonts
        self.font_size = 32
        self.font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", self.font_size)
        self.font_bold = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_fat.ttf", self.font_size)
        self.font_slim = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_slim.ttf", int(self.font_size * 0.9))

        self.font_color_base = (255, 255, 255)
        self.font_color_half = (200, 200, 200, 100)

        self.color_dict = {
            1: (255, 215, 0, 100),
            2: (192, 192, 192, 100),
            3: (205, 127, 50, 100),
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
        self.frame = Image.new(
            'RGBA', (self.frame_w, self.frame_h), (0, 0, 0, 255))

        # Fill background with a non-transparent layer to fix self.frame transparency due to RGBA
        solid_bg = Image.new(
            'RGB', (self.frame_w, self.frame_h), (0, 0, 0))
        bg_image = Image.open('./cogs/replays/render/bg_frame.png')
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=4))
        bg_image_w, bg_image_h = bg_image.size
        bg_image_ratio = self.frame_h / bg_image_h
        if bg_image_ratio < self.frame_w / bg_image_w:
            bg_image_ratio = self.frame_w / bg_image_w
        bg_image = bg_image.resize(
            (int(bg_image_w * bg_image_ratio), int(bg_image_h * bg_image_ratio)))
        solid_bg.paste(bg_image, box=(
            0, 0))
        self.bg = solid_bg
        self.frame.paste(self.bg)
        self.frame_draw = ImageDraw.Draw(self.frame)

    def render_header(self, player_details: dict):
        header_w = self.base_card_w
        header_h = self.header_h
        header_card = Image.new(
            'RGBA', (header_w, header_h), (0, 0, 0, 100))
        header_draw = ImageDraw.Draw(header_card)

        # Render card on frame
        self.frame.paste(header_card, box=(
            self.frame_margin_w, int(self.frame_margin_h / 2)), mask=header_card.split()[3])

    def render_all_stats(self, stats_all: dict, last_stats_all: dict):
        stats_all_w = self.base_card_w
        stats_all_h = self.base_card_h
        stats_all_card = Image.new(
            'RGBA', (stats_all_w, stats_all_h), (0, 0, 0, 100))
        stats_draw = ImageDraw.Draw(stats_all_card)

        # Organize Data
        live_stats_random = last_stats_all.get('live_stats_random')
        live_stats_rating = last_stats_all.get('live_stats_rating')
        last_stats_random = last_stats_all.get('last_stats_random')
        last_stats_rating = last_stats_all.get('last_stats_rating')
        # Session Stats
        session_battles = last_stats_random.get('battles')
        session_dmg_all = last_stats_random.get('damage_dealt')
        session_wins_all = last_stats_random.get('wins')
        session_dmg_avg = f"{round(session_dmg_all / session_battles)}"
        session_wr_avg = f"{round(((session_wins_all / session_battles) * 100), 2)}%"
        session_wn8 = f'WN8: 0000'
        # Live stats
        live_battles = live_stats_random.get('battles')
        live_dmg_all = live_stats_random.get('damage_dealt')
        live_wins_all = live_stats_random.get('wins')
        live_dmg_avg = f"{round(live_dmg_all / live_battles)}"
        live_wr_avg = f"{round(((live_wins_all / live_battles) * 100), 2)}%"
        slive_wn8 = f'WN8: 0000'

        print(session_wr_avg, live_wr_avg)

        # Get text size
        damage_text_w, damage_text_w = stats_draw.textsize(
            'Damage', font=self.font)
        winrate_text_w, winrate_text_w = stats_draw.textsize(
            'Winrate', font=self.font)
        wn8_text_w, wn8_text_w = stats_draw.textsize(
            'WN8', font=self.font_bold)

        # Top row
        # Draw metric names
        draw_name_w = text_w_margin
        draw_name_h = text_h_margin
        stats_draw.text((draw_name_w, draw_name_h), tank_name,
                        self.font_color_base, font=self.font_bold)

        # Render card on frame
        stats_all_render_h = int(
            (self.frame_margin_h / 2) + (self.header_h) + self.card_margin_h)
        self.frame.paste(stats_all_card, box=(
            self.frame_margin_w, stats_all_render_h), mask=stats_all_card.split()[3])

    def render_detailed_stats(self, tank_stats: dict, card_index):
        stats_detailed_w = self.base_card_w
        stats_detailed_h = self.detailed_card_h
        stats_detailed_card = Image.new(
            'RGBA', (stats_detailed_w, stats_detailed_h), (0, 0, 0, 100))
        stats_draw = ImageDraw.Draw(stats_detailed_card)

        # Organize tank data
        tank_name = tank_stats.get('tank_name')
        tank_battles = tank_stats.get("battles")
        tank_survival = round(
            (tank_stats.get('survived_battles') / tank_battles))
        # Performance
        tank_wr = f"WR: {round(((tank_stats.get('wins') / tank_battles) * 100))}% ({tank_battles})"
        tank_dmg = f"DMG: {round((tank_stats.get('damage_dealt') / tank_battles))}"
        tank_xp = f"XP: {round((tank_stats.get('xp') / tank_battles))}"
        tank_wn8 = f"WN8: 0000"
        tank_frags = round((tank_stats.get('frags') / tank_battles))

        # Get text size
        name_text_w, name_text_h = stats_draw.textsize(
            tank_name, font=self.font_bold)
        wr_text_w, wr_text_h = stats_draw.textsize(
            tank_wr, font=self.font)
        xp_text_w, xp_text_h = stats_draw.textsize(
            tank_xp, font=self.font)
        dmg_text_w, dmg_text_h = stats_draw.textsize(
            tank_dmg, font=self.font)
        wn8_text_w, wn8_text_h = stats_draw.textsize(
            tank_wn8, font=self.font_bold)

        # Margins
        text_w_margin = self.text_margin_w
        text_h_margin = int((stats_detailed_h - (name_text_h + wr_text_h)) / 3)
        bottom_metric_margin = int(stats_detailed_w / 3)

        # Top row
        # Draw tank name
        draw_name_w = text_w_margin
        draw_name_h = text_h_margin
        stats_draw.text((draw_name_w, draw_name_h), tank_name,
                        self.font_color_base, font=self.font_bold)
        # Draw tank WN8
        draw_wn8_w = int((stats_detailed_w - wn8_text_w - text_w_margin))
        draw_wn8_h = draw_name_h
        stats_draw.text((draw_wn8_w, draw_wn8_h), tank_wn8,
                        self.font_color_base, font=self.font_bold)
        # Bottom row
        # Draw tank damage
        draw_dmg_w = int((bottom_metric_margin - dmg_text_w) / 2)
        draw_dmg_h = int(stats_detailed_h - dmg_text_h - text_h_margin)
        stats_draw.text((draw_dmg_w, draw_dmg_h), tank_dmg,
                        self.font_color_base, font=self.font)
        # Draw tank xp
        draw_xp_w = int((bottom_metric_margin * 1) +
                        ((bottom_metric_margin - xp_text_w) / 2))
        draw_xp_h = draw_dmg_h
        stats_draw.text((draw_xp_w, draw_xp_h), tank_xp,
                        self.font_color_base, font=self.font)
        # Draw tank winrate
        draw_wr_w = int((bottom_metric_margin * 2) +
                        ((bottom_metric_margin - wr_text_w) / 2))
        draw_wr_h = draw_dmg_h
        stats_draw.text((draw_wr_w, draw_wr_h), tank_wr,
                        self.font_color_base, font=self.font)

        # Render card on frame
        stats_detailed_render_h = int(
            (self.frame_margin_h / 2) + ((2 * self.card_margin_h) + (self.base_card_h + self.header_h)) + (card_index * (stats_detailed_h + self.card_margin_h)))
        self.frame.paste(stats_detailed_card, box=(
            self.frame_margin_w, stats_detailed_render_h), mask=stats_detailed_card.split()[3])

    def render_image(self):
        final_buffer = BytesIO()
        self.frame.save(final_buffer, 'png')
        final_buffer.seek(0)
        image_file = File(
            filename=f"top.png", fp=final_buffer)
        return image_file
