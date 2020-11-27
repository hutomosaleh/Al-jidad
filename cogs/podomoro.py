# Pomodoro.py
import os
import asyncio
from copy import deepcopy
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv



class PomodoroCog(commands.Cog, name='\nPomodoro Commands'):

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.mongodb.pomodoro.log
        self.user = {}

    @commands.command(aliases=['pomodoro', 'belajar'], help='Personal pomodoro timer that logs your sessions!')
    async def study(self, ctx, time=30, pause=5, info=None, *argv):
        user = ctx.author.id
        duration = 0  # duration of the session
        for i in argv:
            info += f" {i}"
        time_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.user[user] = {"s_time": 0, "p_time": 0, "study": True}
        message = await ctx.send(content=f"OK, let's do a {time} minute session with {pause} minute break. Go!")
        while self.user[user]['study']:
            self.user[user] = {"s_time": 0, "p_time": 0, "study": True}
            duration = await self.timer(ctx, time, pause, message, duration)
            self.update_db(ctx, duration, info, time_date)
            if self.user[user]['study'] is True:
                message = await ctx.send(content=f"Hey {ctx.author.mention}! Want to do another session?")
                emojis = {"\U0001f345": "yes", "\U0001f6ab": "no"}
                for key, val in emojis.items():
                    await message.add_reaction(key)

                def check(reac, usr):
                    return usr == ctx.author and str(reac.emoji) is not None

                try:
                    reaction, usr = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    await message.delete()
                    return await ctx.send(content="You're taking too long.. Are you asleep? Go rest for a bit!")
                else:
                    await message.delete()
                    if emojis[str(reaction.emoji)] == "yes":
                        message = await ctx.send(content=f"Nice, lets do a {time} minute session with {pause} minute "
                                                         f"break again!")
                    elif emojis[str(reaction.emoji)] == "no":
                        return await ctx.send(content=f"Great our total session was {duration}, cya later!")
            else:
                return await ctx.send(f"Our total session was {duration} ")

    async def timer(self, ctx, time, pause, message, duration):
        i = self.user[ctx.author.id]
        while i['s_time'] < time and i['study'] is True:
            i['s_time'] += 1
            duration += 1
            await asyncio.sleep(60)
        # play timer sound
        await message.delete()
        if i['study'] is True:
            message = await ctx.send(content=f"Hey {ctx.author.mention}! It's time for a {pause} minute break!")
        while i['p_time'] < pause and i['study'] is True:
            i['p_time'] += 1
            await asyncio.sleep(60)
        if i['study'] is False:
            return duration
        else:
            await message.delete()
            return duration

    def update_db(self, ctx, duration, info, time):
        user = ctx.author.id
        try:
            old_file = self.db.find({"name": user})[0]
            data = deepcopy(old_file)
            data['sessions'][time] = {"duration": duration, "info": info}
            self.db.replace_one(old_file, data)
        except IndexError:
            data = {
                "name": user,
                "sessions": {
                    time: {"duration": duration, "info": info}
                },
            }
            self.db.insert_one(data)
        print("db updated")

    @commands.command(aliases=['stopstudy'], help='Stops your study session!')
    async def stopsession(self, ctx):
        self.user[ctx.author.id]['study'] = False
        await ctx.send(f"Session stopped!")


def setup(bot):
    bot.add_cog(PomodoroCog(bot))
