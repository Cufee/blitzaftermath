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
            replay_data = Replay(replays).gather_all()

            # requests.post('http://localhost:4000/replays', json=replay_data)
            # test = rapidjson.loads(requests.get(f'http://localhost:4000/replays/{replay_id}').text)

            # json_formatted_str = rapidjson.dumps(replay_data, indent=4)
            # print(json_formatted_str)

            # new_message = ''f"{replay_data[0].get('summary').get('player_name')}\n{replay_data[0].get('summary').get('map_name')}"''
            # await message.channel.send(new_message)
            allies = replay_data[0].get('summary').get('allies')
            enemies = replay_data[0].get('summary').get('enemies')

            allies_names = []
            enemies_names = []

            for player in replay_data[0].get('players'):
                player_id = player.get('player_id')
                player_name = player.get(
                    'data').get('all').get('nickname')

                if int(player_id) in allies:
                    allies_names.append(player_name)
                else:
                    enemies_names.append(player_name)

            print(len(allies_names), len(enemies_names))

            # Defining Embed
            # embed_allies = ('\n'.join(allies_names))
            embed_allies = (' \n'.join(allies_names))
            embed_enemies = (' \n'.join(enemies_names))
            embed_stats = 'embed_stats_text'
            embed_footer = "This bot is made and maintained by @Vovko#0851. Let me know if something breaks :)"

            # Constructing Embed
            embed = discord.Embed(title="Aftermath Repplays")
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
