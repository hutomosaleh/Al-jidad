# ragnarok.py
import os
import json
import random
import discord
import asyncio
import youtube_dl
import giphy_client
from datetime import time, datetime, timedelta
from giphy_client.rest import ApiException
from discord.ext import commands
from dotenv import load_dotenv
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

prefix = ['oi ', 'Oi ', 'OI ', 'jid ']
bot_id = ['711125834244554774', '365975655608745985', '709880783325757610']

def read_json(filename):
    file = 'files/' + filename
    with open(file, 'r') as f:
        ro = json.load(f)
    return ro


class RagnaCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.time_to_spawn = None
        self.monster = None
        self.imgr_results = None
        self.spawn_msg = None
        self.users_list = {}
        self.monstername = None
        self.tries = 5

    def __getstate__(self):
        return ({
            'time': self.time_to_spawn,
            'store': self.monster,
            'imgr': self.imgr_results,
            'msg': self.spawn_msg,
            'users': self.users_list
        })
        pass

    def __setstate__(self, dictState):
        self.time_to_spawn = dictState['time']
        self.monster = dictState['store']
        self.imgr_results = dictState['imgr']
        self.spawn_msg = dictState['msg']
        self.users_list = dictState['users']
        pass

    @property
    def time_to_spawn(self):
        return self._time_to_spawn

    @time_to_spawn.setter
    def time_to_spawn(self, value):
        self._time_to_spawn = value

    def getSeconds(self):
        return (self.time_to_spawn - datetime.now()).total_seconds()

    # def setToSpawn(self):
    #     if self.time_to_spawn is None:
    #         return False
    #     else:
    #         return True

    @property
    def appeared(self):
        print("A monster has appeared: {}".format((self.monster is not None)))
        return self.monster is not None

    """
        Commands ==========================================================
    """

    @commands.command(aliases=['ro'], help='summons monster')
    async def oi(self, ctx):
        ro = read_json('ro_ids.json')
        ids, mob = random.choice(list(ro.items()))
        print(mob)
        hint = list(mob)
        for i in range(1, len(hint)):
            if hint[i] == ' ':
                pass
            else:
                hint[i] = ' _'
        hint = ''.join(hint)
        print(hint)
        embed = discord.Embed(title='A monster has appeared!', description='Kill it before it kills you!', color=15158332)
        embed.set_image(url='https://cp.originsro.org/data/images/monsters/{}.gif'.format(ids))
        embed.add_field(name='Starts with the letter', value='\n`{}`'.format(hint), inline=True)
        self.monster = True
        self.monstername = mob.lower()
        await ctx.send(embed=embed)

    """
     Listeners ==========================================================
    """

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bot or wrong channel do nothing
        if message.author == self.bot.user or message.content[1:].startswith("spawn"):  # or message.channel == CHANNEL_IDs:
            return

        # # Pokemon is going to be found
        # if self.setToSpawn():
        #     pass
        # else:
        #     # Pokemon is ready for capture
        #     if self.appeared:
        #         await self.check_capture(message)
        #     else:
        #         pass

        if self.appeared:
            await self.check_capture(message)
        else:
            print('pass')

    """
        Others ==========================================================
    """

    async def check_capture(self, message):
        a = ' ro'
        b = a in message.content
        if self.monster is None or b:
            return False
        if self.monstername == message.content.lower():
            await message.channel.send('You killed the monster!')
            self.monstername = None
            self.monster = None
            self.tries == 5
            return True
        else:
            self.tries -= 1
            if self.tries == 0:
                await message.channel.send('You lost and died a horrible death!')
                self.monstername = None
                self.monster = None
                self.tries == 5
                return True
            else:
                await message.channel.send('You missed and got attacked!')

        return False


def setup(bot):
    bot.add_cog(RagnaCog(bot))

