import rapidjson
import os

import discord
from discord.ext import commands, tasks
from itertools import cycle
from cogs.core_logger.logger import Logger

logger = Logger()

# Startup
with open(f'{os.path.dirname(os.path.realpath(__file__))}/settings.json') as f:
    settings = rapidjson.load(f)
TOKEN = settings["TOKEN"]
prefix = settings["prefix"]
default_game = settings["default_game"]
client = commands.Bot(command_prefix=prefix, case_insensitive=False, activity=discord.Game(name=default_game))
client.remove_command('help')

# Load cogs
for filename in os.listdir(f'{os.path.dirname(os.path.realpath(__file__))}/cogs'):
    if filename.endswith('.py'):
        if filename.startswith('core_'):
            client.load_extension(f'cogs.{filename[:-3]}')
            logger.log(f'{filename[:-3]} was loaded')
            continue
        # cog_settings = settings.get(filename[:-3])
        # cog_name = cog_settings.get('name')
        # is_enabled = cog_settings.get(f'enabled_{mode}')
        is_enabled = True  # Need to replace once hooked up to db
        if is_enabled:
            client.load_extension(f'cogs.{filename[:-3]}')
            logger.log(f'{filename} was loaded')
        else:
            logger.log(f'{filename} is disabled')

# Startup
@client.event
async def on_ready():
    logger.log(f'{client.user.name} online!')

# Errors
@client.event
async def on_command_error(ctx, error):
    pass

# Cog managment
@client.command(hidden=True)
@commands.is_owner()
async def info(ctx):
    await ctx.message.delete()
    await ctx.send(f'Message: {ctx.message.id} [{ctx.message.channel}: {ctx.message.channel.id}]\nGuild: {ctx.message.guild.id}', delete_after=10)


@client.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    await ctx.message.delete()
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Loaded {extension} extension.', delete_after=10)


@client.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension='null'):
    await ctx.message.delete()
    if extension == 'null':
        await ctx.send(f'No extension name specified.', delete_after=10)
    else:
        client.unload_extension(f'cogs.{extension}')
        await ctx.send(f'Unloaded {extension} extension.', delete_after=10)


@client.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension='null'):
    await ctx.message.delete()
    if extension == 'null':
        await ctx.send(f'No extension name specified.', delete_after=10)
    else:
        client.unload_extension(f'cogs.{extension}')
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Reloaded {extension} extension.', delete_after=10)


@client.command(hidden=True)
@commands.is_owner()
async def listcogs(ctx):
    await ctx.message.delete()
    cogs = []
    for filename in os.listdir(f'{os.path.dirname(os.path.realpath(__file__))}/cogs'):
        if filename.endswith('.py'):
            cogs.append(f'{filename[:-3]}')
    await ctx.send(f'Found these cogs:\n{cogs}', delete_after=10)


# Run
client.run(TOKEN)
