# ragnarok.py
import os
import json
import random
import discord
import asyncio
import requests
from discord.ext import commands

directory = 'files/savefile/'
RO_url = 'https://www.divine-pride.net/api/database/'
RO_TOKEN = os.getenv('RO_TOKEN')


def save_json(filename, file):
    with open(directory + filename, 'w') as f:
        json.dump(file, f, indent=2, sort_keys=False)


def read_json(filename):
    with open('{}{}'.format(directory, filename), 'r') as f:
        savefile = json.load(f)
    return savefile


def save_monster_data(mob_id):
    mob_dir = 'files/RO/monsters_data/' + f'{mob_id}.json'
    if not os.path.exists(mob_dir):
        response = requests.get(RO_url + f'Monster/{mob_id}?apiKey={RO_TOKEN}')
        with open(mob_dir, 'w') as f:
            json.dump(response.json(), f, indent=2, sort_keys=False)
        print('RO JSON File saved!')


class RagnaCog(commands.Cog, name='\nRagnarok Commands'):

    def __init__(self, bot):
        self.bot = bot
        self.quest = {}
        self.spawn_msg = None
        self.savefile = read_json('ragnarok.json')
        self.stats = self.savefile["ids"]
        self.job = self.savefile["job_change"]

    """
        Commands ==========================================================
    """

    @commands.command(aliases=['ro', 'RO', 'Ro', 'rO', 'ragna'], help='Go on a quest')
    async def quest(self, ctx):
        ro = read_json('ro_ids.json')
        ids, mob = random.choice(list(ro.items()))
        print(mob)
        hint = list(mob)
        channel = str(ctx.channel.id)
        for i in range(1, len(hint)):
            if hint[i] == ' ':
                pass
            else:
                hint[i] = ' _'
        hint = ''.join(hint)
        print(hint)
        embed = discord.Embed(title='A monster has appeared!', description='Kill it before it kills you!', color=15158332)
        embed.add_field(name='Starts with the letter', value='\n`{}`'.format(hint), inline=True)
        file = discord.File(f'files/RO/monsters/{ids}.gif', filename=f'{ids}.gif')
        embed.set_image(url=f'attachment://{ids}.gif')
        await ctx.send(file=file, embed=embed)
        save_monster_data(ids)
        self.quest[channel] = {}
        self.quest[channel]["channel"] = int(channel)
        self.quest[channel]["monster"] = mob.lower()
        self.quest[channel]["summoner"] = ctx.message.author.id
        self.quest[channel]["tries"] = 5

    @commands.command(help='Shows your RO stats')
    async def status(self, ctx):
        player = str(ctx.message.author.id)
        try:
            playerstats = self.stats[player]
            gender = playerstats["gender"][0]
            job = playerstats["job"].lower()
            file = discord.File(f'files/RO/Job 1/1 {job} {gender}.gif', filename=f'0 nov {gender}.gif')
            embed = discord.Embed(title='Your adventurer status', description=' ',
                                  color=15158332)
            embed.add_field(name='Name: ', value='{}'.format(playerstats['name']), inline=True)
            embed.add_field(name='Job: ', value='{}'.format(playerstats['job']), inline=True)
            # embed.add_field(name='\u200b', value='\u200b')  # invisible field to push the fields
            embed.add_field(name='Level: ', value='{}'.format(playerstats['level']), inline=True)
            embed.add_field(name='Exp: ', value='{}'.format(playerstats['exp']), inline=True)
            file = discord.File(f'files/RO/Job 1/1 {job} {gender}.gif', filename=f'0 {job} {gender}.gif')
            embed.set_image(url='attachment://{}'.format(f'0 {job} {gender}.gif'))
            await ctx.send(file=file, embed=embed)
        except KeyError:
            await ctx.send("You're not in the adventurers guild. Please register first!")

    @commands.command(help='Register yourself to the adventurers guild')
    async def register(self, ctx, name=None):
        if name is None:
            await ctx.send("Please include your name!")
        elif str(ctx.author.id) in self.stats:
            await ctx.send("You're already in our list!")
        else:
            message = await ctx.send("Are you male or female?")
            await message.add_reaction('\U00002642\U0000fe0f')
            await message.add_reaction('\U00002640\U0000fe0f')

            def check(reac, usr):
                return usr == ctx.author and (str(reac.emoji) == '\U00002642\U0000fe0f' or str(reac.emoji) == '\U00002640\U0000fe0f')
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("We've got people waiting in line, come back later once you've made up your mind!")
            else:
                if str(reaction.emoji) == '\U00002642\U0000fe0f':
                    gender = "male"
                else:
                    gender = "female"
                self.registration(ctx.message.author.id, name, gender)
                await ctx.send(f"Congratulations {name}, you're an adventurer!")

    @commands.command(help='Leave the adventurers guild for good')
    async def leave(self, ctx):
        if str(ctx.author.id) in self.stats:
            message = await ctx.send("Are you completely sure about leaving us?")
            await message.add_reaction('\U0001f44d')
            await message.add_reaction('\U0001f44e')

            def check(reac, usr):
                return usr == ctx.author and (str(reac.emoji) == '\U0001f44d' or str(reac.emoji) == '\U0001f44e')

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=20.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Hesitating huh... I knew you don't actually want to leave!")
            else:
                if str(reaction.emoji) == '\U0001f44e':
                    await ctx.send("Good thing you decided to stay, we still need you!")
                else:
                    await ctx.send("We'll miss you, {}".format(str(self.stats[str(ctx.author.id)]["name"])))
                    del self.stats[str(user.id)]
                    self.update_json()
        else:
            await ctx.send("You're not even in the guild!")

    @commands.command(aliases=["change"], help='Change your job')
    async def jobchange(self, ctx):
        player = self.stats[str(ctx.author.id)]
        jobs = ['Swordsman', 'Acolyte', 'Archer', 'Merchant', 'Thief', 'Magician']
        number_emoji = ['%d\N{variation selector-16}\N{combining enclosing keycap}' % int(i+1) for i in range(6)]
        if player["job"] == "Novice" and player["level"] >= self.job["Novice"]:
            msg = "Congratulations, you can now advance your job! Please choose any of the jobs below!\n\n"
            embed = discord.Embed()
            file = discord.File('files/RO/job_change.gif', filename='job_change.gif')
            embed.set_image(url='attachment://job_change.gif')
            option = "Swordsman\nAcolyte\nArcher\nMerchant\nThief\nMagician"
            await ctx.send(msg)
            message = await ctx.send(file=file, embed=embed)
            # message = await ctx.send("\u200b")
            for i in range(6):
                await message.add_reaction(number_emoji[i])

            def check(reac, usr):
                return str(reac.emoji) in number_emoji and usr == ctx.author

            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("Seems like you're having a hard time deciding, maybe you should think about it alone at home!")
            decision = {}
            for i in range(6):
                decision[number_emoji[i]] = jobs[i]
            player['job'] = decision[str(reaction.emoji)]
            await ctx.send(f"Congratulations! You're now a {player['job']}")
            self.update_json()
        else:
            await ctx.send("You're level is too low!")

    @commands.command(hidden=True)
    @commands.has_role('admin')
    async def levelup(self, ctx):
        self.stats[str(ctx.author.id)]['level'] += 10
        self.update_json()
        await ctx.send("You leveled up!")

    @commands.command(hidden=True)
    @commands.has_role('admin')
    async def print(self, ctx):
        print(self.stats)
        self.stats[str(ctx.author.id)]["exp"] += 2000
        await ctx.send(str(self.stats[str(ctx.author.id)]["exp"]))
        self.update_json()

    """
     Listeners ==========================================================
    """

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bot or wrong channel do nothing
        if message.author.bot:  # or message.channel == CHANNEL_IDs:
            if message.content[1:].startswith("spawn"):
                return
            return

        if self.quest_active(message):

            await self.check_killed(message)
            # try:
            #     await asyncio.wait_for(self.check_killed(message), timeout=5.0)
            # except asyncio.TimeoutError:
            #     self.monster = None
            #     await message.channel.send("Monster killed you before you even killed it!")

        else:
            pass

    """
        Others ==========================================================
    """

    def quest_active(self, message):
        try:
            if self.quest[str(message.channel.id)]:
                return True
        except KeyError:
            return False


    async def check_killed(self, message):
        print("Checking kill")
        a = ' ro'
        b = a in message.content
        if message.author.nick is None:
            player = str(message.author)[:-5]
        else:
            player = message.author.nick
        try:
            quest = self.quest[str(message.channel.id)]
            print(self.quest)
            if quest["monster"] is None or b:
                return False
            if quest["monster"] == message.content.lower() and quest["channel"] == message.channel.id:
                if message.author.id is not quest["summoner"]:
                    await message.channel.send('Monster has been KS-ed by {}!'.format(player))
                else:
                    await message.channel.send('{} killed {}!'.format(player, quest["monster"]))
                self.quest[str(message.channel.id)] = None
                await self.exp_increase(message)
                return True
            else:
                quest["tries"] -= 1
                if quest["tries"] == 0:
                    await message.channel.send('{} lost and died a horrible death!'.format(player))
                    await self.exp_decrease(message)
                    self.quest[str(message.channel.id)] = None
                    return True
                else:
                    await message.channel.send('{} missed and got attacked!'.format(player))
            return False
        except KeyError:
            print("KeyError")
            return False

    async def exp_increase(self, message):
        if str(message.author.id) in self.stats:
            player = self.stats[str(message.author.id)]
            exp = player["exp"]
            name = player["name"]
            exp_gained = 2000
            player["exp"] += exp_gained
            await message.channel.send('{} gained {} Exp!'.format(name, exp_gained))
            level = player["level"]
            exp_cap = self.savefile["exp"][str(level)]
            if exp > exp_cap:
                player["exp"] = abs(int(exp_cap - exp))
                player["level"] += 1
                await message.channel.send("You leveled up!")
            self.update_json()
            print(player["exp"])
            return True
        else:
            await message.channel.send("You're strong! You should register yourself to the adventurer's guild!")
            return True

    async def exp_decrease(self, message):
        try:
            player = self.stats[str(message.author.id)]
            exp = player["exp"]
            name = player["name"]
            exp_lost = int(0.1 * self.savefile["exp"][str(player["level"])])
            player["exp"] -= exp_lost
            if player["exp"] < 0:
                player["exp"] = 0
                await message.channel.send('{} lost {} Exp...'.format(name, 0))
            else:
                await message.channel.send('{} lost {} Exp...'.format(name, exp_lost))
            self.update_json()
        except KeyError:
            return True
            # await message.channel.send("Help! Help! Someone revive him!")

    def registration(self, userid, name, gender):
        info = {
            "name": name,
            "id": userid,
            "job": "Novice",
            "gender": gender,
            "exp": 0,
            "level": 1
        }
        self.stats[str(userid)] = info
        self.update_json()

    def update_json(self):
        try:
            save_json('ragnarok.json', self.savefile)
        except Exception as Err:
            print(Err)
        print("Game saved!")


def setup(bot):
    bot.add_cog(RagnaCog(bot))

