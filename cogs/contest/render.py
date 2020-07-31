from operator import itemgetter
from dataclasses import dataclass

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from discord import File
from io import BytesIO

import requests
import rapidjson

from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError

client = MongoClient(
    "mongodb+srv://vko:XwufAAtwZh2JxR3E@cluster0-ouwv6.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = client.summer2020contest

clans = db.clans
players = db.players


class Render:
    def __init__(self, top_count=5):
        self.top_count = top_count
        self.top_clans_list = list(clans.find().sort(
            'clan_aces', -1).limit(top_count))

        self.render_prep()
        for i in range(top_count):
            self.render_clan_card((i-1))

    def render_prep(self):
        self.frame_margin_w = 50
        self.frame_margin_h = 50
        self.clan_card_w = 400
        self.clan_card_h = 60
        self.text_margin_w = 5
        self.text_margin_h = 10
        self.frame_w = (self.frame_margin_w*2) + self.clan_card_w
        self.frame_h = (self.frame_margin_h*2) + \
            (self.clan_card_h * self.top_count)\

        self.frame = Image.new(
            'RGBA', (self.frame_w, self.frame_h), (0, 0, 0, 255))

        solid_bg = Image.new('RGB', (self.frame_w, self.frame_h), (0, 0, 0))

        bg_image = Image.open('./cogs/replays/render/bg_frame.png')
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

        # Import fonts
        self.font_size = 20
        self.font = ImageFont.truetype(
            "./cogs/replays/render/fonts/font.ttf", self.font_size)
        self.font_fat = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_fat.ttf", (int(self.font_size * 1.25)))
        self.font_slim = ImageFont.truetype(
            "./cogs/replays/render/fonts/font_slim.ttf", self.font_size)

        self.font_color_base = (255, 255, 255)

        self.color_dict = {
            0: (230, 180, 0, 100),
            1: (192, 192, 192, 100),
            2: (205, 127, 50, 100),
        }

    def render_clan_card(self, card_index):
        self.card = Image.new(
            'RGBA', (self.clan_card_w, self.clan_card_h), (128, 128, 128, 100))
        draw = ImageDraw.Draw(self.card)
        ace_icon = Image.open(
            f'./cogs/replays/render/icons/mastery_badge_4.png')
        ace_icon_size = round(self.clan_card_h * .66)
        ace_icon = ace_icon.resize((ace_icon_size, ace_icon_size))

        # Draw clan data
        clan_data = self.top_clans_list[card_index + 1]
        clan_tag = f'[{clan_data.get("clan_tag")}]'
        clan_name = clan_data.get('clan_name')
        clan_aces = clan_data.get('clan_aces')
        best_clan_aces = self.top_clans_list[-1].get('clan_aces')

        tag_w, tag_h = draw.textsize(clan_tag, font=self.font)
        name_w, name_h = draw.textsize(clan_name, font=self.font)
        aces_w, aces_h = draw.textsize(str(clan_aces), font=self.font)
        best_aces_w, best_aces_h = draw.textsize(
            str(best_clan_aces), font=self.font)

        tag_draw_h = round(
            (self.clan_card_h - tag_h - name_h) / 3)
        tag_draw_w = tag_draw_h * 2
        draw.text((tag_draw_w, tag_draw_h), clan_tag,
                  self.font_color_base, font=self.font)

        name_draw_w = tag_draw_w
        name_draw_h = (tag_draw_h * 2) + tag_h
        draw.text((name_draw_w, name_draw_h), clan_name,
                  self.font_color_base, font=self.font)

        ace_draw_w = self.clan_card_w - (tag_draw_w) - aces_w
        ace_draw_h = round((self.clan_card_h - aces_h) / 2)
        draw.text((ace_draw_w, ace_draw_h), str(clan_aces),
                  self.font_color_base, font=self.font)

        ace_icon_draw_w = self.clan_card_w - \
            ace_icon_size - (best_aces_w*2)
        ace_icon_draw_h = round((self.clan_card_h - ace_icon_size) / 2) + 4
        self.card.paste(ace_icon, box=(ace_icon_draw_w,
                                       ace_icon_draw_h), mask=ace_icon.split()[3])

        # Add rating color stripes
        card_color = self.color_dict.get(
            (card_index + 1), None)
        if card_color:
            rating_box_w1 = 0
            rating_box_h1 = 0
            rating_box_w2 = 5
            rating_box_h2 = self.clan_card_h

            draw.rectangle([(rating_box_w1, rating_box_h1),
                            (rating_box_w2, rating_box_h2)], fill=card_color)

        # Add card to frame
        card_render_w = round((self.frame_w - self.clan_card_w) / 2)
        card_render_h = round(
            (((self.frame_margin_h) * 2) + self.text_margin_h + (card_index * (self.clan_card_h + self.text_margin_h) - self.text_margin_h)))

        self.frame.paste(self.card, box=(
            card_render_w, card_render_h), mask=self.card.split()[3])

    def render_image(self):
        final_buffer = BytesIO()
        self.frame.save(final_buffer, 'png')
        final_buffer.seek(0)
        image_file = File(
            filename=f"top.png", fp=final_buffer)
        return image_file
