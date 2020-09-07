from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import sys
import traceback
from datetime import datetime


class clan_activity(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath Clan Activity cog is ready.')

    # Commands
    # @commands.command(aliases=['', ''])

    # Commands
    @commands.command(aliases=[])
    async def clan(self, ctx, *args):
        if ctx.author == self.client.user:
            return

        clan_str = "".join(args).strip()
        if "@" in clan_str:
            # Realm was specified
            clan_str = clan_str.split("@")
            clan_tag = clan_str[0].upper()
            clan_realm = clan_str[-1].upper()

            full_url = "http://localhost:10000/clans/" + clan_tag
            res = requests.get(full_url)
            if res.status_code != 200:
                error_msg = rapidjson.loads(res.text).get("error", "")
                await ctx.send(f"Error [{res.status_code}] {error_msg}")
                return
            res_data = rapidjson.loads(res.text)

            clan_data = res_data.get("clan_data")
            players_data = res_data.get("players")
            if not players_data:
                await ctx.send(f"It looks like {clan_data.get('clan_name')} have not played a single battle yet.")
                return

            header = f"**Session info for {clan_data.get('clan_name')}**"
            legend = f"*Nickname - Battles Total [WN8] / Session [WN8]*\n"

            body = []
            for player in players_data:
                body.append(f'{player.get("nickname")} - {player.get("battles")} [{player.get("average_rating")}] / **{player.get("session_battles")}** [{player.get("session_rating")}]')
            body = "\n".join(body)

            await ctx.send("\n".join([header, legend, body]))

        else:
            # No realm specified
            await ctx.send("Not implemented, please specify @server")
            return


def setup(client):
    client.add_cog(clan_activity(client))
