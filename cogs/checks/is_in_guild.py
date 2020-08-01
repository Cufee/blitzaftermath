from discord.ext import commands


def is_in_guild(guild_id):
    async def predicate(ctx):
        return ctx.guild.id == guild_id
    return commands.check(predicate)
