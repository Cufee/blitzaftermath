from discord.ext import commands, tasks
from cogs.replays.replay import Replay
import discord

import rapidjson
import requests
import re

from cogs.replays.replay import Replay

# WG API setup
wg_application_id = 'application_id=add73e99679dd4b7d1ed7218fe0be448'
wg_api_base_url = 'https://api.wotblitz.com/wotb/account/'
wg_api_addon_list = 'list/?'
wg_api_addon_info = 'info/?'
wg_api_realm = 'r_realm=na'


class blitz_aftermath_replays(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Replays cog is ready.')

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        channel_name = message.channel.name
        attachments = message.attachments

        # Verify channel
        # if message.channel.id != 719875141047418962:
        if message.channel.id != 719831153162321981 and message.channel.id != 719875141047418962:
            return

        replays = []
        if attachments:
            print('valid message')

            for attachment in attachments:
                if attachment.url.endswith('.wotbreplay'):
                    replays.append(attachment.url)

            # Send replay to WoTInspector
            replays_list_data = Replay(replays).process_replays()

            replay_data = replays_list_data.get(
                list(replays_list_data.keys())[0])

            map_name = replay_data.get('battle_summary').get('map_name')
            winner_team = replay_data.get('battle_summary').get('winner_team')

            protagonist_id = replay_data.get(
                'battle_summary').get('protagonist')
            protagonist_data = replay_data.get(
                'players').get(str(protagonist_id))

            battle_result = 'Win'
            if winner_team != 1:
                battle_result = 'Loss'

            allies_names = []
            enemies_names = []

            for player in replay_data.get('players'):
                data = replay_data.get('players').get(player)
                if data.get('team') == 2:
                    enemies_names.append(data.get('nickname'))
                else:
                    allies_names.append(data.get('nickname'))

            # Protagonist performance
            pr_performance = protagonist_data.get('performance')
            pr_vehicle_stats = protagonist_data.get('vehicle_stats')

            pr_battle_dmg = pr_performance.get(
                'damage_made')
            pr_stats_avg_dmg = round(pr_vehicle_stats.get(
                'damage_dealt') / pr_vehicle_stats.get('battles'))

            pr_battle_kills = pr_performance.get(
                'enemies_destroyed')
            pr_stats_avg_kills = round(pr_vehicle_stats.get(
                'frags8p') / pr_vehicle_stats.get('battles'))

            pr_battle_shots = pr_performance.get(
                'shots_made')
            pr_battle_pen = pr_performance.get(
                'shots_pen')

            embed_stats_text = (
                f'Damage vs Career {pr_battle_dmg}/{pr_stats_avg_dmg}\n' +
                f'Kills vs Career {pr_battle_kills}/{pr_stats_avg_kills}\n' +
                f'Shots vs Pen {pr_battle_shots}/{pr_battle_pen}')

            # Defining Embed
            embed_allies = (' \n'.join(allies_names))
            embed_enemies = (' \n'.join(enemies_names))
            embed_stats = embed_stats_text

            embed_footer = f"MD5/ID: {list(replays_list_data.keys())[0]}"

            replay_link = 'https://www.google.com/'

            # Constructing Embed
            embed = discord.Embed(
                title="Click here for detailed results", url=replay_link)
            embed.set_author(name="Aftermath Replays")
            embed.add_field(
                name="Allies", value=f'```{embed_allies} ```', inline=False)
            embed.add_field(
                name="Enemies", value=f'```{embed_enemies} ```', inline=False)
            embed.add_field(
                name="Stats", value=f'```{embed_stats}```', inline=False)
            embed.set_footer(text=embed_footer)

            # Send message
            await message.channel.send(embed=embed)
            return


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))
