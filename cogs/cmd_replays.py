from discord.ext import commands, tasks
from cogs.replays.replay import Replay
from cogs.replays.rating import Rating
import discord

import rapidjson
import requests
import re

from cogs.replays.replay import Replay
from cogs.replays.render import Render

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
            replay_id = list(replays_list_data.keys())[0]

            replay_data = Rating(replay_data).calculate_rating('mBRT1_0')
            embed = Render(replay_data, replay_id).embed()

            # Send message
            await message.channel.send(embed=embed)
            return


def setup(client):
    client.add_cog(blitz_aftermath_replays(client))
