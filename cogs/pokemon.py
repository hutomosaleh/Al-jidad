# pokemon.py
import os
import sys
import json
import random
import discord
import asyncio
import youtube_dl
import giphy_client
from giphy_client.rest import ApiException
from discord.ext import commands
from dotenv import load_dotenv
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup


"""
    Other functions
"""

directory = 'files/savefile/'


def save_json(filename, file):
    with open('{}'.format(directory)+filename, 'w') as f:
        json.dump(file, f, indent=2, sort_keys=False)


def read_json(filename):
    with open('{}{}'.format(directory, filename), 'r') as f:
        savefile = json.load(f)
    return savefile


def txt_to_array(filename):
    file = 'files/txt/' + filename
    with open(file, 'r') as f:
        x = f.readlines()
        d = []
        for i in range(len(x)):
            c = x[i].replace('\n', '')
            d.append(c)
    return d


"""
    Commands
"""


class PokeCog(commands.Cog, name='Pokemon Commands \n'):

    def __init__(self, bot):
        self.bot = bot
        self.quest = {}
        self.spawn_msg = None
        self.savefile = read_json('pokemon.json')
        self.caught = self.savefile['pokemon_caught']

    @commands.command(aliases=['pokemon'], help='look for pokemons')
    async def catch(self, ctx):
        ro = txt_to_array('poke_list.txt')
        mob = random.choice(ro).title()
        print(mob)
        hint = list(mob)
        channel = str(ctx.channel.id)
        print(channel)
        for i in range(1, len(hint)):
            if hint[i] == ' ':
                pass
            else:
                hint[i] = ' _'
        hint = ''.join(hint)
        print(hint)
        old_name = os.path.join("files/pokemon/original/", f"{mob.lower()}.gif")
        new_name = os.path.join("files/pokemon/original/", "jidad.gif")
        os.rename(old_name, new_name)
        embed = discord.Embed(title='You found a pokemon!', description='Catch it before it runs!',
                              color=12320855)
        embed.add_field(name='Starts with the letter',
                        value=f'\n`{hint}`', inline=True)
        file = discord.File(
            f'files/pokemon/original/jidad.gif', filename='jidad.gif')
        embed.set_image(url=f'attachment://jidad.gif')
        await ctx.send(file=file, embed=embed)
        os.rename(new_name, old_name)
        try:
            self.quest[channel]
        except KeyError:
            self.quest[channel] = {}
            self.quest[channel]["trainer"] = {}
        self.quest[channel]["trainer"]["id"] = str(ctx.message.author.id)
        self.quest[channel]["trainer"]["pokemon"] = mob.lower()
        self.quest[channel]["trainer"]["tries"] = 5

    async def check_catch(self, message):
        print("Checking catch")
        if message.author.nick is None:
            player = str(message.author)[:-5]
        else:
            player = message.author.nick
        try:
            quest = self.quest[str(message.channel.id)]["trainer"]
            print(self.quest)
            if quest["pokemon"] is None:
                return False
            if quest["pokemon"] == message.content.lower():
                await message.channel.send(f'{player} caught {quest["pokemon"]}!')
                self.caught_pokemon(message)
                quest["pokemon"] = None
            else:
                quest["tries"] -= 1
                if quest["tries"] == 0:
                    await message.channel.send('The Pokémon ran away!')
                    quest["pokemon"] = None
                    return True
                else:
                    await message.channel.send(f'{player} missed the Poké Ball!')
            return False
        except KeyError as Err:
            print(Err)

    """
     Listeners ==========================================================
    """

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bot or wrong channel do nothing
        if message.author.bot or message.content[3:].startswith("catch"):
            return
        elif str(message.channel.id) not in self.quest:
            return
        elif self.quest_active(message):
            # if str(message.author.id) not in self.quest[str(message.channel.id)]["trainer"]["id"]:
            #     return
            # else:
            #     await self.check_catch(message)
            await self.check_catch(message)
        else:
            return

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        self.update_json()

    """
        Others
    """

    def update_json(self):
        try:
            save_json('pokemon.json', self.savefile)
        except Exception as Err:
            print(Err)
        print("Game saved!")

    def quest_active(self, message):
        try:
            if self.quest[str(message.channel.id)]:
                return True
        except KeyError:
            return False

    def caught_pokemon(self, message):
        quest = self.quest[str(message.channel.id)]["trainer"]
        try:
            self.caught[str(message.author.id)]
        except KeyError:
            self.caught[str(message.author.id)] = {}
        poke_id = self.caught[str(message.author.id)]
        try:
            poke_id[quest["pokemon"]] += 1
        except KeyError:
            poke_id[quest["pokemon"]] = 0
            poke_id[quest["pokemon"]] += 1
        self.update_json()


def setup(bot):
    bot.add_cog(PokeCog(bot))
