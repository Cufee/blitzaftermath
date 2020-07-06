from discord.ext import commands, tasks
from cogs.replays.replay import Replay
import discord

import rapidjson
import requests
import re

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
        if message.author == self.client.user: return
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

            # await message.channel.send(f'```{str(replay_data)[:1000]}...```')

            new_message = f"{replay_data[0].get('summary').get('player_name')}\n{replay_data[0].get('summary').get('map_name')}"

            await message.channel.send(new_message)
            
            # # Defining Embed
            # embed_allies = ('\n'.join(allies))
            # embed_enemies = ('\n'.join(enemies))
            # embed_stats = embed_stats_text
            # embed_footer = "This bot is made and maintained by @Vovko #0851. Let me know if something breaks :)" + f'\n{min_x}, {max_x}, {middle_line}, {len(all_predictions)}'

            # # Constructing Embed
            # embed=discord.Embed(title="Support Blitz Aftermath", url="https://www.paypal.me/vovko", description="If you would like to support me, click the link above.")
            # embed.add_field(name="Allies", value=f'```{embed_allies}```', inline=False)
            # embed.add_field(name="Enemies", value=f'```{embed_enemies}```', inline=False)
            # embed.add_field(name="Stats", value=f'```{embed_stats}```', inline=False)
            # embed.set_footer(text=embed_footer)

            # # Send message
            # await message.channel.send(embed=embed)
            # return


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))