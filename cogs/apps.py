# apps.py
import os
import json
import random
import discord
import asyncio
import requests
import pymongo
from PIL import Image
from pymongo import MongoClient
from discord.ext import commands
from dotenv import load_dotenv
from asyncio import *
from aiohttp import ClientSession, ClientTimeout, TCPConnector

dict_file = "files/txt/de_en.txt"

load_dotenv()
TKN_MONGODB = os.getenv('MONGO_DB')
client = MongoClient(TKN_MONGODB)


def search_dict(keyword):
    with open(dict_file, mode='r', encoding='utf-8') as f:
        keyword = keyword.lower()
        keywords = [f" {keyword} ", f"-{keyword} ", f" {keyword}-"]
        result = []
        for line in f:
            line_check = f" {line.lower()}"
            if keywords[0] in line_check or keywords[1] in line_check or keywords[2] in line_check:
                result.append(line)
                result = sorted(result, key=lambda e: len(e))  # sorts by length

        # sort result and its meanings
        words = []
        meanings = []
        desc = []
        translation = {}
        for i in result:
            res = i.split("\t")
            new_word = res[0]
            words.append(res[0])
            meanings.append(res[1])
            if res[-1] != "\n":
                desc.append(res[-1].split("\n")[0])
            else:
                desc.append("")
            try:
                if new_word != old_word and not translation[new_word]:
                    translation[new_word] = [res[1]]
                elif new_word == old_word:
                    translation[old_word].append(res[1])
            except (UnboundLocalError, KeyError):
                translation[new_word] = [res[1]]
            old_word = res[0]

    return translation


async def network_session(url):
    async with ClientSession() as session:
        html = await gather(network_get(url, session))
    return html


async def network_get(url, session):
    if url:
        while True:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return str(await response.content.read())
                    await sleep(1)
            except Exception as e:
                print(e)
    else:
        return True



class AppsCog(commands.Cog, name='\nOther Application Commands'):

    def __init__(self, bot):
        self.bot = bot
        self.db = client.horoscope.sign
        self.savefile = self.db.find()[0]

    @commands.command(help='translates german words to english')
    async def translate(self, ctx, keyword, limit=5):
        translation = search_dict(keyword)
        print(keyword)
        # txt = "```py" + "\n" + "Translation results: \n\n"
        txt = "```\n"
        items = 0
        for key, value in translation.items():
            items += 1
            meanings = value[0]
            line_lim = 0
            for i in value[1:]:
                line_lim += 1
                if line_lim == 7:
                    meanings += f"\n\t\t\t {i}"
                    line_lim = 0
                else:
                    meanings += f", {i}"
            txt += f"{key}: {meanings} \n\n"
            if items == limit:
                break
        print(txt)
        txt += "```"
        if txt == "```\n```":
            txt = "```No translations found, try another word```"
        await ctx.send(txt)

    @commands.command(help='ramalan / horoscopemu hari ini')
    async def ramal(self, ctx, sign=None):
        user = str(ctx.message.author.id)
        if sign is None:
            try:
                sign = self.savefile[user]
            except KeyError:
                message = await ctx.send("``` Pick your sign! ```")
                emojis = {"\U0001f411": "aries", "\U0001f402": "taurus", "\U0001f46f": "gemini",
                          "\U0001f980": "cancer", "\U0001f981": "leo", "\U0001f469": "virgo",
                          "\U00002696": "libra", "\U0001f982": "scorpio", "\U0001f3f9": "sagittarius",
                          "\U0001f410": "capricorn", "\U0001f964" : "aquarius", "\U0001f38f": "pisces"}
                for key, val in emojis.items():
                    await message.add_reaction(key)

                def check(reac, usr):
                    return usr == ctx.author and str(reac.emoji) is not None
                try:
                    reaction, usr = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("You're taking too long to answer, how can you not know your zodiac!")
                else:
                    zodiac = emojis[str(reaction.emoji)]
                    self.savefile[user] = zodiac
                    self.db.replace_one(self.db.find()[0], self.savefile)
                    await ctx.send(f"```Your zodiac is {zodiac} and you are registered!```")

        url = f"https://www.astrology.com/horoscope/daily/today/{sign}.html"
        html = await network_session(url)
        txt = html[0].split("<p><span class=")[1].split("</span>")[1].split("</p>")[0].replace('\\', "")
        embed = discord.Embed(title=f'{sign.capitalize()}', description=txt, color=0x261A16)
        file = discord.File(f'files/astrology/{sign}.jpg', filename=f'{sign}.jpg')
        embed.set_image(url='attachment://{}'.format(f'{sign}.jpg'))
        await ctx.send(file=file, embed=embed)


    @commands.command(help='ramalan / tarotmu hari ini')
    async def tarot(self, ctx, sign=None):
        db = client.horoscope.tarot
        random_card = random.randint(0, db.estimated_document_count()-1)
        random_side = random.choice(['upright', 'reverse'])
        file = db.find()[random_card]
        if sign is None:
            sign = 'general'
        else:
            for i in [i for i in file['content'][random_side].keys()]:
                if sign in i.lower():
                    print(i)
                    sign = i
        title = f'{file["name"].upper()}'
        try:
            txt = file['content'][random_side][sign].replace(r"\xe2\x80\x99", "'").replace(';', '')\
                .replace(r"\xe2\x80\x9c", '"').replace(r"\xe2\x80\x9d", '"')
        except KeyError:
            await ctx.send("Please specify either of these choices: 'love', 'health', 'money', 'spirit'")
        embed = discord.Embed(title=title, description=txt, color=0x1AA6FA)
        jpg_name = f'files/tarot/{file["name"].replace(" ", "-")}.jpg'
        if random_side == 'reverse':
            img = Image.open(jpg_name)
            img = img.transpose(method=Image.FLIP_TOP_BOTTOM)
            jpg_name = f"{jpg_name[:-4]}-reverse.jpeg"
            img.save(jpg_name)
            img.close()
        img_file = discord.File(jpg_name, filename=f'{file["name"]}.jpg')
        embed.set_image(url='attachment://{}'.format(f'{file["name"].replace(" ", "-")}.jpg'))
        await ctx.send(embed=embed, file=img_file)


def setup(bot):
    bot.add_cog(AppsCog(bot))


