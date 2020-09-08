from discord.ext import commands, tasks
import discord
import requests
import rapidjson
import sys
import traceback
from datetime import datetime
from operator import itemgetter


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

            clan_dict = {
                "clan_tag" : clan_tag,
                "realm": clan_realm
            }

            full_url = "http://localhost:10000/clan"
            res = requests.get(full_url, json=clan_dict)
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

            players_data = sorted(players_data, key=itemgetter('session_battles'), reverse=True) 

            header = f"**Session info for {clan_data.get('clan_name')}**"
            legend = f"```Nickname{(' ' * (16 - len('Nickname')))}Battles WN8```"

            body = ["```"]
            for player in players_data:
                player_str = f'{player.get("nickname")}{(" " * (18 - len(player.get("nickname"))))}{player.get("session_battles")}{(" " * (4 - len(str(player.get("session_battles")))))}{player.get("session_rating")}'
                if player.get("session_rating") > player.get("average_rating"):
                    player_str += " ˄"
                elif player.get("session_rating") < player.get("average_rating"):
                    player_str += " ˅"

                body.append(player_str)
            body.append("```")
            body = "\n".join(body)

            await ctx.send("\n".join([header, legend, body]))

        else:
            # No realm specified
            await ctx.send("Not implemented, please specify @server")
            return


def setup(client):
    client.add_cog(clan_activity(client))
