import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix=['oi ', 'Oi ', 'OI ', 'jid '])

startup_extensions = ['cogs.simple', 'cogs.ragnarok', 'cogs.pokemon', 'cogs.apps']


@bot.event
async def on_ready():
    print('==============')
    print('Jidad is ready')
    print('==============')


if __name__ == '__main__':
    for extension in startup_extensions:
        bot.load_extension(extension)

bot.run(TOKEN, bot=True, reconnect=True)
