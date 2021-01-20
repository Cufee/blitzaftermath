from discord.ext import commands
from datetime import datetime

from cogs.api.guild_settings_api import API_v2

command_cooldown = 5

debug = False
Guilds_API = API_v2()

class maintenance(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Events
    # @commands.Cog.listener()
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'[Beta] Aftermath maintenance cog is ready.')

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        guild_id = str(guild.id)
        guild_name = str(guild.name)
        _, status_code = Guilds_API.add_new_guild(guild_id, guild_name)

        await self.report_to_owner(f"Aftermath joined {guild_name}. Setup complete with `{status_code}`.")
        return

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        guild_id = str(guild.id)
        guild_name = str(guild.name)
        new_settings = {"kicked_on": datetime.utcnow()}
        _, status_code = Guilds_API.update_guild(guild_id, new_settings, safe=False)

        await self.report_to_owner(f"Aftermath was removed from {guild_name}. Edit complete with `{status_code}`.")

def setup(client):
    client.add_cog(maintenance(client))
