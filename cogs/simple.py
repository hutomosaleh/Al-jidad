# bot.py
import os
import sys
import json
import random
import asyncio
import discord
import youtube_dl
import giphy_client
import requests
import pandas as pd
from io import StringIO
from collections import defaultdict
from giphy_client.rest import ApiException
from discord.ext import commands
from dotenv import load_dotenv
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

load_dotenv()

GIPHY_TOKEN = os.getenv('GIPHY_TOKEN')
api_instance = giphy_client.DefaultApi()
gd_film = r"https://docs.google.com/spreadsheets/d/e/2PACX-1vQnT4GMCJ2QGVF7hLuvNVZdlziBMXijwRKT5InRfFLhNVO9lm8rprDIhjIRqrLqyczFNUrnTKHWNMJK/pub?output=csv"
gd_game = r"https://docs.google.com/spreadsheets/d/e/2PACX-1vQqUAcn0YDwNc5ADJqiDeO02sO58aQMJGyAM-z-PB_8jvtylBMXsFgCqRs28tzqwsPJ5-_ALvYdqF8w/pub?output=csv"
gd_flag = r"https://docs.google.com/spreadsheets/d/e/2PACX-1vQFaSUWgq4jU6QYq5Xr2PPcU_EVKWTQot8ARfnKLUSDMZZe6_jCTCz7Se_qrVyFjm4k8fmoFJqcPal-/pub?output=csv"
gd_instrument = r"https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8EdTnhLWN8CSTtnTjde2IBwQSPZw-E7KTROXp0rF0qai_L90tZMRnItB6v5aXvyTCjh64dpRF6kK1/pub?output=csv"

'''
    Other functions
'''


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
Giphy Setup ======================================================================
"""

config = {
    'api_key': GIPHY_TOKEN,  # Giphy API Key,
    'query': 'cheese',
    'limit': 1,
    'rating': 'g'
}


async def search_gifs(query):
    try:
        response = api_instance.gifs_search_get(GIPHY_TOKEN, query, limit=10, rating='g')
        lst = list(response.data)
        gif = random.choices(lst)
        if len(gif) == 0:
            d = 'https://giphy.com/gifs/rupaulsdragrace-rupauls-drag-race-season-11-XcddSHiizbz0IzlLJJ'
            return d
        else:
            return gif[0].url

    except ApiException as e:
        return "Exception when calling DefaultApi->gifs_search_get: %s\n" % e


"""
Youtube Downloader ======================================================================
"""

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

nama_belakang = {'<@163320354662514688>': 'Kusuma Wardhani', '<@690190849182924859>': 'Tandya', '<@690210811003666435>': 'Muliawan',
                 '<@690190783952715851>': 'Halim', '<@149466509926727682>': 'Angdjaja',
                 '<@691671675812708364>': 'Setiawan', '<@690209627907948612>': 'Muliawan',
                 '<@325596713358458891>': 'Saleh', '<@450770327686086656>': 'Agustin'}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


"""
Web Scraper ======================================================================
"""


def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors.
    This function just prints them, but you can
    make it do anything.
    """
    print(e)


"""
Commands ======================================================================
"""


class MainCog(commands.Cog, name='Main Commands'):
    
    def __init__(self, bot):
        self.db_trivia = bot.mongodb.trivia
        self.bot = bot
        self.tebak_list = defaultdict(dict)
        self.tebak_list['film'] = self.open_drive(gd_film)
        self.tebak_list['game'] = self.open_drive(gd_game)
        self.tebak_list['flag'] = self.open_drive(gd_flag)
        self.tebak_list['instrument'] = self.open_drive(gd_instrument)
        self.tebak_info = defaultdict(dict)


    @commands.command(aliases=['version'], help='cek trakhir kali update')
    async def update(self, ctx, keyword):
        await ctx.send('Last update: 14/05/2020 23:10 CET')


    @commands.command(aliases=['kadoin'], help='kasih kado random')
    async def gift(self, ctx, recipient):
        filename = random.choice(os.listdir('files/gifts'))
        pic = 'files/gifts/{}'.format(filename)
        file = discord.File(pic, filename=filename)
        embed = discord.Embed(title='Yeayy dapet kado!!', description=' ', color=16580705)
        embed.add_field(name='Dengan kasih sayang', value=str(ctx.message.author)[:-5], inline=True)
        embed.add_field(name='Untuk yang tercinta', value=recipient, inline=True)
        embed.set_image(url='attachment://{}'.format(filename))
        await ctx.send(file=file, embed=embed)

    @commands.command(help='a lil scare to wake u up')
    async def spook(self, ctx):
        filename = random.choice(os.listdir('files/spook'))
        pic = 'files/spook/{}'.format(filename)
        file = discord.File(pic, filename=filename)
        embed = discord.Embed()
        embed.set_image(url='attachment://{}'.format(filename))
        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=['house'], help='rumah impianmu')
    async def rumah(self, ctx):
        if str(ctx.message.author.id) in ['690210811003666435', '690209627907948612']:
            folders = ['spooky']
        else:
            folders = ['nice']
        directory = random.choice(folders)
        filename = random.choice(os.listdir('files/houses/{}'.format(directory)))
        pic = 'files/houses/{}/{}'.format(directory, filename)
        file = discord.File(pic, filename=filename)
        embed = discord.Embed(title='Rumah yang cocok untukmu', description=' ', color=16580705)
        embed.add_field(name='Milik', value=str(ctx.message.author)[:-5], inline=True)
        embed.set_image(url='attachment://{}'.format(filename))
        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=['room'], help='kamar yang cocok untukmu')
    async def kamar(self, ctx):
        filename = random.choice(os.listdir('files/oi kamar'))
        pic = 'files/oi kamar/{}'.format(filename)
        file = discord.File(pic, filename=filename)
        embed = discord.Embed(title='Kamar yang cocok untukmu', description=' ', color=16580705)
        embed.add_field(name='Milik', value=str(ctx.message.author)[:-5], inline=True)
        embed.set_image(url='attachment://{}'.format(filename))
        await ctx.send(file=file, embed=embed)

    @commands.command(help='cute animals')
    async def kyot(self, ctx):
        filename = random.choice(os.listdir('files/oi kyot'))
        pic = 'files/oi kyot/{}'.format(filename)
        file = discord.File(pic, filename=filename)
        embed = discord.Embed(title=' ', description=' ', color=16580705)
        embed.set_image(url='attachment://{}'.format(filename))
        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=['binatang'], help='summon your inner creature')
    async def creature(self, ctx):
        filename = random.choice(os.listdir('files/oi creature'))
        pic = 'files/oi creature/{}'.format(filename)
        file = discord.File(pic, filename=filename)
        embed = discord.Embed(title='Your inner spirit...', description=' ', color=16580705)
        # embed.add_field(name=' ', value=str(ctx.message.author)[:-5] + "", inline=True)
        embed.set_image(url='attachment://{}'.format(filename))
        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=['makan'], help='hidangan spesial untukmu')
    async def food(self, ctx):
        filename = random.choice(os.listdir('files/oi food'))
        pic = 'files/oi food/{}'.format(filename)
        file = discord.File(pic, filename=filename)
        embed = discord.Embed(title='Selamat menikmati', description=' ', color=16580705)
        embed.add_field(name='Milik', value=str(ctx.message.author)[:-5], inline=True)
        embed.set_image(url='attachment://{}'.format(filename))
        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=['main', 'youtube'], help='dengerin video youtube')
    async def mainin(self, ctx, what, *argv):
        user = ctx.message.author
        voice_channel = user.voice
        channel = None
        # only play music if user is in a voice channel
        if voice_channel is not None:
            # grab user's voice channel
            voice_channel = voice_channel.channel
            await ctx.send('yo')
            # create StreamPlayer
            await voice_channel.connect()

        arg = []
        web = 'https://www.youtube.com/results?search_query={}'.format(what)
        for i in argv:
            arg.append(i)
            web += '+' + str(i)

        raw_html = simple_get(web)
        soup = BeautifulSoup(raw_html, 'lxml')
        a = soup.find_all('a', attrs={'class': 'yt-uix-tile-link'})
        videolist = []
        for v in a:
            tmp = 'https://www.youtube.com' + v['href']
            videolist.append(tmp)

        url = videolist[0]
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        vidname = 'youtube-' + url[len('https://www.youtube.com/watch?v='):] + '-' + player.title.replace(' ',
                                                                                                          '_') + '.webm'
        await ctx.send('Nemu ni {}'.format(player.title))
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=player.title))
        while ctx.voice_client.is_playing():
            await asyncio.sleep(1)
        # disconnect after the player has finished
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        os.remove(vidname)

    @commands.command(aliases=['pls', 'fun'], help='gifs gifs gifs')
    async def gif(self, ctx, what, *argv):
        for arg in argv:
            what += f"-{arg}"
        gif = await search_gifs(what)
        await ctx.send(gif)

    @commands.command(help='Saran film')
    async def film(self, ctx, opt=None):
        horror = txt_to_array('oi_film_horror.txt')
        all_films = horror
        if opt == 'horror':
            await ctx.send('Sp00ky film for u: {}'.format(random.choice(horror)))
        else:
            await ctx.send('I recommend: {}'.format(random.choice(all_films)))

    @commands.command(name="nama", aliases=['anakku'], help='memberimu sebuah nama anak')
    async def nama(self, ctx, opt=None):
        first = txt_to_array('1st_names.txt')
        midlast = txt_to_array('2nd_names.txt')
        r = random.choice
        c = ['', '']
        c[0] = r(first)
        c[1] = r(midlast)
        easter = random.randint(1, 1000)
        userid = '<@{}>'.format(ctx.message.author.id)
        Lastname = ''
        a = random.randint(1, 5)
        a = 1
        if a == 1:
            if userid in nama_belakang:
                Lastname = nama_belakang[userid]
        if easter == 500:
            await ctx.send('WIS KESEL AKU CUK, KEAKEAN NYROCOS CANGKEM MU')
            await ctx.send('BANGSAT')
            await search_gifs('angry')
            await ctx.message.guild.leave()
        else:
            await ctx.send('Nama anakmu ' + c[0] + ' ' + c[1] + ' ' + Lastname)

    @commands.command(name='bilangapa', help='coba aja')
    async def bilangapa(self, ctx):
        await ctx.send('makasih kk')

    @commands.command(aliases=['chess'], help='buat main catur')
    async def catur(self, ctx):
        await ctx.send('https://www.chess.com/home')

    @commands.command(name='google', help='buka link google')
    async def google(self, ctx, what, *argv):
        arg = []
        msg = 'https://www.google.com/search?hl=en&q={}'.format(what)
        for i in argv:
            arg.append(i)
            msg += '+' + str(i)
        await ctx.send(msg)

    @commands.command(name='dadu', help='main dadu')
    async def roll(self, ctx, number_of_dice: int, number_of_sides: int):
        dice = [
            str(random.choice(range(1, number_of_sides + 1)))
            for _ in range(number_of_dice)
        ]
        await ctx.send(', '.join(dice))

    @commands.command(name='cuk', aliases=['jancok', 'bangsat'], pass_context=True, help='ngegas balik')
    async def cuk(self, ctx):
        userid = '<@{}>'.format(ctx.message.author.id)
        # userid = '<@149466509926727682>'
        msg = txt_to_array('oi_cuk.txt')
        r = random.randint(1, 2)
        name = random.choice(msg)
        message = 'oi {} '.format(userid) + name
        if r == 2:
            message = message.upper()
        await ctx.send(message)
        # await ctx.message.author.edit(nick=name)

    @commands.command(name='sini', aliases=['rene'], pass_context=True, help='ramein voice chat')
    async def join(self, ctx):
        if ctx.message.author.voice:
            channel = ctx.message.author.voice.channel
            await channel.connect()

    @commands.command(name='pergi', aliases=['stop'], pass_context=True, help='ngusir al-jidad')
    async def leave(self, ctx):
        if ctx.message.author.voice:
            server = ctx.message.guild.voice_client
            await server.disconnect()

    @commands.command(name='brpsih', help='ngitung pertambahan, perkalian, pembagian')
    async def calc(self, ctx, no1: int, arg: str, no2: int):
        perkalian = ['tambah', 'plus', '+']
        bego = 'lah'
        if arg == 'kali' or arg == 'x' or arg == '*':
            result = no1 * no2
        elif arg in perkalian:
            result = no1 + no2
        elif arg == 'bagi' or arg == '%':
            if no1 == 0 and no2 == 0:
                result = 'duh gatau'
            elif no2 == 0:
                result = 'tak terhingga'
            else:
                result = round(no1 / no2, 4)
        await ctx.send(str(result) + ' ' + bego)

    @commands.command(name='jidad', pass_context=True, help='mainin coffin dance')
    async def coffin(self, ctx, opt=None):
        # grab the user who sent the command
        user = ctx.message.author
        voice_channel = user.voice
        channel = None
        # only play music if user is in a voice channel
        if opt == 'stop':
            if ctx.message.author.voice:
                server = ctx.message.guild.voice_client
                await server.disconnect()
        elif voice_channel is not None:
            # grab user's voice channel
            voice_channel = voice_channel.channel
            await ctx.send('yo')
            # create StreamPlayer
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source='coffin.mp3'))
            await self.bot.change_presence(
                activity=discord.Activity(type=discord.ActivityType.listening, name='to coffin dance'))
            while vc.is_playing():
                await asyncio.sleep(1)
            # disconnect after the player has finished
            vc.stop()
            await vc.disconnect()
        else:
            await ctx.send('ape')

    @commands.command(aliases=['guess'], help='A guessing game')
    async def tebak(self, ctx, *args):
        user = ctx.message.author.id
        db = self.db_trivia.film
        if len(args) == 0:
            return await ctx.send("Specify what you want to guess! (film, game, am, flag)")

        for identifier in args:
            if identifier == 'am':
                identifier = 'instrument'
            await self.tebak_identifier(identifier, ctx)

    async def tebak_identifier(self, identifier, ctx):
        channel_id = ctx.channel.id
        self.tebak_info[channel_id][identifier] = {'active': False, 'title': None}
        filename = random.choice(os.listdir(f'files/oi tebak/{identifier}'))
        pic = f'files/oi tebak/{identifier}/{filename}'
        num = pic.split('.')[0].split('/')[-1]
        if num[-1].isalpha():  # removes alphabet
            num = num[:-1]
        num = int(num)
        embed = discord.Embed(title='Guess!', description=f"What {identifier} is this?", color=0x261A16)
        file = discord.File(pic, filename=filename)
        embed.set_image(url=f'attachment://{filename}')
        self.tebak_info[channel_id][identifier]['active'] = True
        await ctx.send(file=file, embed=embed)

        # answer
        title = r"{}".format(str(self.tebak_list[identifier].iloc[num - 1]))
        print(title)
        title = title.split('\n')[0].split('Title')[-1].split(' ')
        print(title)
        title_new = []
        for i, val in enumerate(title):
            if val != '':
                title_new.append(val)
        print(title)
        title = ' '.join([str(elem) for elem in title_new])
        title = title.replace(':', '').replace(' -', '').replace("'", '').replace("?", '').replace("-", '').replace("!", '')
        self.tebak_info[channel_id][identifier]['title'] = title
        print(title)

    def open_drive(self, url):
        r = requests.get(url)
        data = r.content.decode('utf-8')
        return pd.read_csv(StringIO(data), index_col=0)

    async def add_points(self, message, channel, trivia):
        print('adding points')
        user = message.author.id
        db = self.db_trivia.film
        if not db.find_one({'user': user}):
            db.insert_one({
                'user': user,
                'points': 0
            })
        old_point = db.find_one({'user': user})['points']
        db.update_one(
            {'user': user},
            {"$set": {'points': old_point+1}}
        )
        if (old_point+1) % 10 == 0:
            filename = random.choice(os.listdir('files/oi tebak/gift'))
            pic = f'files/oi tebak/gift/{filename}'
            embed = discord.Embed(title='Congratulations!', description="Here's your prize!", color=0x261A16)
            file = discord.File(pic, filename=filename)
            embed.set_image(url=f'attachment://{filename}')
            await message.channel.send(file=file, embed=embed)
        self.tebak_info[channel][trivia] = {'active': False, 'title': None}
        return await message.channel.send(
            f"{str(message.author).split('#')[0]} guessed it right! \n"
            f"You now have {db.find_one({'user': user})['points']} Points!"
        )

    @commands.command(name='restart')
    @commands.has_role('admin')
    async def cmd_restart(self, ctx, message=None):
        await ctx.channel.send('Restarting...')
        await self.bot.close()
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(name="jawab")
    async def tebak_jawaban(self, ctx):
        print(self.tebak_info)

    """
        Listeners ==========================================================
    """

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel.id
        trivia = ['film', 'game', 'instrument', 'flag']
        msg = message.content.lower()
        msg = msg.replace(':', '').replace(' -', '').replace("'", '').replace("?", '').replace("-", '')
        # Bot or wrong channel do nothing
        if message.author.bot:  # or message.channel == CHANNEL_IDs:
            return

        try:
            for i in trivia:
                if self.tebak_info[channel][i]['active']:
                    if self.tebak_info[channel][i]['title'].lower() == msg:
                        return await self.add_points(message, channel, i)
        except KeyError:
            return
        return


def setup(bot):
    bot.add_cog(MainCog(bot))
