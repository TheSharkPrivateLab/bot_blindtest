import asyncio
import discord
from time import time, ctime, sleep
from discord.ext import commands
from database import Database

if not discord.opus.is_loaded():
	# the 'opus' library here is opus.dll on windows
	# or libopus.so on linux in the current directory
	# you should replace this with the location the
	# opus library is located in and with the proper filename.
	# note that on windows this DLL is automatically provided for you
	discord.opus.load_opus('opus')

def sort(points : dict):
	key = list()
	for i in points:
		key.append(i)
	if len(points) <= 1:
		return key
	i = 1
	while i != len(points):
		if points[key[i - 1]] < points[key[i]]:
			temp = key[i - 1]
			key[i - 1] = key[i]
			key[i] = temp
			i = 0
		i += 1
	return key

class VoiceEntry:
	def __init__(self, message, player):
		self.requester = message.author
		self.channel = message.channel
		self.player = player

	def __str__(self):
		fmt = '*something* uploaded by {0.uploader} and requested by {1.display_name}'
		duration = self.player.duration
		if duration:
			fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
		return fmt.format(self.player, self.requester)

class VoiceState:
	def __init__(self, bot):
		self.current = None
		self.voice = None
		self.bot = bot
		self.play_next_song = asyncio.Event()
		self.songs = asyncio.Queue()
		self.skip_votes = set() # a set of user_ids that voted
		self.audio_player = self.bot.loop.create_task(self.audio_player_task())

	def is_playing(self):
		if self.voice is None or self.current is None:
			return False

		player = self.current.player
		return not player.is_done()

	@property
	def player(self):
		return self.current.player

	def skip(self):
		self.skip_votes.clear()
		if self.is_playing():
			self.player.stop()

	def toggle_next(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

	async def audio_player_task(self):
		while True:
			self.play_next_song.clear()
			self.current = await self.songs.get()
			await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
			self.current.player.start()
			await self.play_next_song.wait()

class Clock:
	def __init__(self):
		self.start_time = None

	def __str__(self):
		if self.start_time is None:
			return "Clock has not started yet."
		msg = "Started time : {0[0]}h {0[1]}m {0[2]}s\n".format(self.time_to_list(self.start_time))
		msg += "Elapsed time : {0[0]}h {0[1]}m {0[2]}s".format(self.get_elapsed_time())
		return msg

	def start(self):
		self.start_time = self.get_time()

	def stop(self):
		self.start_time = None

	def restart(self):
		return self.start()

	def time_to_list(self, time):
		result = list()
		for i in range(3):
			result.append(int((time / 60 ** i) % 60))
		temp = result[0]
		result[0] = result[2]
		result[2] = temp
		return result

	def get_elapsed_time(self):
		time = self.get_elapsed_time_s()
		result = self.time_to_list(time)
		return result

	def get_elapsed_time_s(self):
		result = self.get_time() - self.start_time
		return result

	def get_time(self):
		temp = ctime(time())
		temp = temp[11:-5]
		liste = list()
		for i in temp.split(':'):
			liste.append(int(i))
		result = int()
		result += liste[2]
		result += liste[1] * 60
		result += liste[0] * (60 ** 2)
		return result

class SongEntry:
	def __init__(self, **args):
		self.requester = args['ctx'].message.author
		self.channel = args['ctx'].message.channel
		self.args = args
		self.clock = Clock()
		self.time_max = 15

	def __str__(self):
		fmt =  " __id__  : **{id}**\n"
		fmt += "__name__ : **{name}**\n"
		if self.args['op'] > 0:
			fmt += " __op__  : **{op}**\n"
			fmt += "__type__ : **{type}**\n"
			fmt += "__link__ : **{link}**"
			return fmt.format(**self.args)

class SongState:
	def __init__(self, bot):
		self.started = False
		self.state = VoiceState(bot)
		self.current = None
		self.volume = 0.6
		self.bot = bot
		self.points = dict()
		self.keys = dict()
		self.play_next_song = asyncio.Event()
		self.reponse = asyncio.Event()
		self.songs = asyncio.Queue()
		self.reponse_task = self.bot.loop.create_task(self.get_reponse())
		self.audio_player = self.bot.loop.create_task(self.audio_player_task())

	def unload(self):
		try:
			while not self.songs.empty():
				self.songs.get_nowait()
		except:
			pass
		self.state.skip()

	def skip(self):
		self.state.skip()

	def toggle_next(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)
		self.state.toggle_next()

	async def get_reponse(self):
		self.reponse.clear()
		while True:
			msg = None
			await self.reponse.wait()
			if self.current is not None:
				await self.bot.send_message(self.current.channel, '**YOU HAVE {}s !!**'.format(self.current.time_max))
				fonction = ['$skip', '$stop']
				test_fonction = False
				test_none     = False
				test_time     = False
				test_same     = False
				msg = self.current.args['ctx'].message
				self.current.clock.start()
				while not test_time and not test_none and not test_same and not test_fonction:
					msg = await self.bot.wait_for_message(timeout=self.current.time_max - self.current.clock.get_elapsed_time_s(), channel=self.current.channel)
					if msg is None:
						test_none = True
					else:
						test_fonction = msg.content in fonction and msg.author.id == self.current.requester.id
						test_time = self.current.clock.get_elapsed_time_s() >= self.current.time_max
						test_same = self.current.args['name'].lower() == msg.content.lower()
				if test_none or test_time:
					await self.bot.send_message(self.current.channel, 'Sorry, that was {0}.'.format(self.current.args['name']))
				elif not test_fonction:
					if self.points.get(msg.author.id) is None:
						self.points[msg.author.id] = 0
						self.keys[msg.author.id] = msg.author
					self.points[msg.author.id] += 1
					txt = '{0.mention} found the truth in {1[2]}'
					await self.bot.send_message(self.current.channel, txt.format(msg.author, self.current.clock.get_elapsed_time()))
				if self.songs.empty():
					msg = 'That was the last song...\n'
					msg += 'Thanks for playing !\n'
					await self.bot.send_message(self.current.channel, msg)
					msg = '------**Score :**------\n'
					keys = sort(self.points)
					for i,key in zip(range(len(self.points)), keys):
						msg += '{0} : {1.mention} With **{2}** points !\n'.format(i + 1, self.keys[key], self.points[key])
					await self.bot.send_message(self.current.channel, msg)
					self.started = False
			self.state.skip()
			self.reponse.clear()

	async def audio_player_task(self):

		opts = {
			'default_search': 'auto',
			'quiet': True,
		}

		while True:
			self.play_next_song.clear()
			temp = await self.songs.get()
			try:
				player = await self.state.voice.create_ytdl_player(temp['link'], ytdl_options=opts, after=self.toggle_next)
			except Exception as e:
				fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
				embed = discord.Embed(title='Error', description='/!\\Entry error/!\\')
				embed.add_field(name='id', value=temp['id'])
				embed.add_field(name='name', value=temp['name'])
				embed.add_field(name='op', value=temp['op'])
				embed.add_field(name='type', value=temp['type'])
				embed.add_field(name='link', value=temp['link'])
				await self.bot.send_message(temp['ctx'].message.channel, fmt.format(type(e).__name__, e), embed=embed)
			else:
				self.current = SongEntry(**temp)
				player.volume = self.volume
				entry = VoiceEntry(temp['ctx'].message, player)
				await self.state.songs.put(entry)
				self.bot.loop.call_soon_threadsafe(self.reponse.set)
			await self.play_next_song.wait()

class DatabaseManager:
	def __init__(self, bot, db_name):
		self.bot = bot
		self.database = Database(db_name)
		self.categorie = self.get_categorie()

	def get_categorie(self):
		self.categorie = self.database.getcategorie()

	@commands.command(pass_context=True, no_pm=False)
	async def addentry(self, ctx, name : str, types : str, link : str, op=0):
		"""Add a link to the link database

		Need 4 parameters to work:
		A name, the opening/ending number, the type (OST, OPENING, etc) and the link
		check this link to see all the supported site :
		https://rg3.github.io/youtube-dl/supportedsites.html
		"""
		msg = await self.bot.say('Starting...')
		message = "Complete !"
		if (self.database.addentry(name, op, link, types) == 1):
			message = "Error: Entry already in the database."
		await self.bot.edit_message(msg, message)

	@commands.command(pass_context=True, no_pm=False)
	async def listdb(self, ctx):
		"""List every entry from the database"""
		msg = await self.bot.say('Collecting information...')
		data = self.database.getall()
		if len(data) == 0:
			await self.bot.edit_message(msg, 'No entry.')
			return

		for i in data:
			embed = discord.Embed(title=i['name'], type='rich', description=i['link'])
			embed.add_field(name='id', value=i['id'])
			embed.add_field(name='op', value=i['op'])
			embed.add_field(name='type', value=i['type'])

			await self.bot.say(embed=embed)

		await self.bot.edit_message(msg, 'Done !')

	@commands.command(pass_context=True, no_pm=False)
	async def delentry(self, ctx, id : int):
		"""Delete one entry from the database."""
		msg = await self.bot.say('deleting entry {}...'.format(id))
		self.database.deleteone(id)
		await self.bot.edit_message(msg, 'Entry successfully deleted !')

	@commands.command(pass_context=True, no_pm=False)
	async def listcategorie(self, ctx):
		"""List all of the categories in the database.

		To add a category, just add a song to the database with this category.
		"""
		msg = await self.bot.say('Collecting informations...')

		self.get_categorie()

		if self.categorie is None:
			await self.bot.edit_message(msg, 'No entry.')
			return

		embed = discord.Embed(name='Categorie', description='List of every category', type='rich')

		categorie = str()

		for i in self.categorie:
			categorie += i
			categorie += '\n'

		embed.add_field(name='Categorie',value=categorie)

		await self.bot.edit_message(msg, ' ',embed=embed)

	@commands.command(pass_context=True, no_pm=False)
	async def listbycategorie(self, ctx, categorie : str):
		"""List by categories"""
		msg = await self.bot.say('Collecting informations...')

		self.get_categorie()
		if self.categorie is None:
			await self.bot.edit_message(msg, 'No entry.')
			return

		if categorie not in self.categorie:
			await self.bot.edit_message(msg, 'Unknow categorie.')
			return

		data = self.database.getfromcategorie(categorie)
		if data is None:
			await self.bot.edit_message(msg, 'No entry in this categorie.')
			return

		for i in data:
			embed = discord.Embed(title=i['name'], type='rich', description=i['link'])
			embed.add_field(name='id', value=i['id'])
			embed.add_field(name='op', value=i['op'])
			embed.add_field(name='type', value=i['type'])

			await self.bot.say(embed=embed)

		await self.bot.edit_message(msg, 'Done !')

class Blindtest:
	"""Voice related commands.

	Works in multiple servers at once.
	"""
	def __init__(self, bot, bdd_name):
		self.bot = bot
		self.voice_states = {}
		self.Blindtest_states = {}
		self.database = Database(bdd_name)

	def get_songs_state(self, server):
		state = self.voice_states.get(server.id)
		if state is None:
			state = SongState(self.bot)
			self.voice_states[server.id] = state

		return state

	def get_voice_state(self, server):
		state = self.get_songs_state(server)

		return state.state

	async def create_voice_client(self, channel):
		voice = await self.bot.join_voice_channel(channel)
		state = self.get_voice_state(channel.server)
		state.voice = voice

	def __unload(self):
		for state in self.voice_states.values():
			try:
				state.state.audio_player.cancel()
				if state.state.voice:
					self.bot.loop.create_task(state.state.voice.disconnect())
			except:
				pass

	def get_categorie(self):
		self.categorie = self.database.getcategorie()

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	async def test(self, ctx):
		"""just a test"""
		msg = 'PENIS\n'
		for i in ctx.message.mentions:
			msg += i.name
			msg += '\n'
		await self.bot.say(msg)

	@commands.command(pass_context=True, no_pm=True, hidden=True)
	async def smiley(self, ctx, nb : int):
		"""just for fun"""
		if ctx.message.author.id == 177447810726232064:
			msg = await self.bot.say('NON !')
			sleep(2)
			await self.bot.delete_message(msg)
		try:
			await self.bot.delete_message(ctx.message)
		except:
			pass
		msg = str()
		for i in range(nb):
			msg += "'-"
			for x in range(i):
				msg += ' '
			msg += "'\n"
		try:
			await self.bot.say(msg)
		except:
			for i in range(nb):
				msg = str()
				msg += "'-"
				for x in range(i):
					msg += ' '
				msg += "'\n"
				await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True, no_pm=True)
	async def start(self, ctx, *categorie):
		"""Start a Blindtest

		you can select multiple categories if you want to
		"""

		self.get_categorie()
		state = self.get_songs_state(ctx.message.server)

		if state.state.voice is None:
			success = await ctx.invoke(self.summon)
			if not success:
				return

		if state.started:
			await self.bot.say('Blindtest already started ! join #`{}` and :speaker:`{}` to participate =)'.format(state.current.args['ctx'].message.channel.name, state.state.voice.channel.name))
			return
		else:
			msg = await self.bot.say('Collecting Music...')
			if len(categorie) == 0:
				one = self.database.getallrandom()
			else:
				for i in categorie:
					if i not in self.categorie:
						await self.bot.edit_message(msg, 'No categorie named {}'.format(i))

				temp = list()
				one  = list()

				for i in categorie:
					temp.append(self.database.getfromcategorierandom(i))
				for i in temp:
					for x in i:
						one.append(x)

				one = tuple(one)

			if one is None:
				await self.bot.edit_message(msg, 'No entry.')
				return
			for i in one:
				i['ctx'] = ctx
				await state.songs.put(i)
				#await self.play(ctx, i['link'])
			state.started = True
			await self.bot.edit_message(msg, 'Done !')

	@commands.command(pass_context=True, no_pm=True)
	async def join(self, ctx, *, channel : discord.Channel):
		"""Joins a voice channel."""
		try:
			await self.create_voice_client(channel)
		except discord.ClientException:
			await self.bot.say('Already in a voice channel...')
		except discord.InvalidArgument:
			await self.bot.say('This is not a voice channel...')
		else:
			await self.bot.say('Ready to play audio in ' + channel.name)

	@commands.command(pass_context=True, no_pm=True)
	async def summon(self, ctx):
		"""Summons the bot to join your voice channel."""
		summoned_channel = ctx.message.author.voice_channel
		if summoned_channel is None:
			await self.bot.say('You are not in a voice channel.')
			return False

		state = self.get_voice_state(ctx.message.server)
		if state.voice is None:
			state.voice = await self.bot.join_voice_channel(summoned_channel)
		else:
			await state.voice.move_to(summoned_channel)

		return True

	@commands.command(pass_context=True, no_pm=True)
	async def volume(self, ctx, value : int):
		"""Sets the volume of the currently playing song."""

		state = self.get_songs_state(ctx.message.server)
		if state.state.is_playing():
			player = state.state.player
			player.volume = value / 100
			state.volume = value / 100
			await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

	@commands.command(pass_context=True, no_pm=True)
	async def pause(self, ctx):
		"""Pauses the currently played song."""
		state = self.get_voice_state(ctx.message.server)
		if state.is_playing():
			player = state.player
			player.pause()

	@commands.command(pass_context=True, no_pm=True)
	async def resume(self, ctx):
		"""Resumes the currently played song."""
		state = self.get_voice_state(ctx.message.server)
		if state.is_playing():
			player = state.player
			player.resume()

	@commands.command(pass_context=True, no_pm=True)
	async def stop(self, ctx):
		"""Stops playing audio and leaves the voice channel.

		This also clears the queue.
		"""
		server = ctx.message.server
		state = self.get_songs_state(server)

		if state.state.is_playing():
			player = state.state.player
			player.stop()

		try:
			state.state.audio_player.cancel()
			del self.voice_states[server.id]
			await state.state.voice.disconnect()
		except:
			pass

		state.unload()

		state.started = False

	@commands.command(pass_context=True, no_pm=True)
	async def skip(self, ctx):
		"""Vote to skip a song. The song requester can automatically skip.

		3 skip votes are needed for the song to be skipped.
		"""

		state = self.get_songs_state(ctx.message.server)
		if not state.state.is_playing() or state.started == False:
			await self.bot.say('Not playing any music right now...')
			return

		voter = ctx.message.author
		if voter == state.current.requester:
			await self.bot.say('Requester requested skipping song...')
			state.skip()
		else:
			await self.bot.say('You are not allowed to do that ! (only {} can do it).'.format(state.current.requester.mention))

	@commands.command(pass_context=True, no_pm=True)
	async def playing(self, ctx):
		"""Shows info about the currently played song."""

		state = self.get_voice_state(ctx.message.server)
		if state.current is None:
			await self.bot.say('Not playing anything.')
		else:
			skip_count = len(state.skip_votes)
			await self.bot.say('Now playing {} [skips: {}/3]'.format(state.current, skip_count))

BDD = 'bdd.db'

muted = dict()

@commands.command(pass_context=True, no_pm=True)
async def mute(ctx, seconde : int):
	"""Mute somoone"""
	global muted
	users = ctx.message.mentions
	server = ctx.message.server
	for i in users:
		if muted[server.id].get(i.id) is not None:
			await bot.say('{0.mention} already muted'.format(i))
		else:
			muted[server.id][i.id] = (Clock(), seconde)
			muted[server.id][i.id][0].start()
			await bot.say('{0.mention} muted !'.format(i))

bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'), description='The Blindtest Bot =)')
bot.add_cog(DatabaseManager(bot, BDD))
bot.add_cog(Blindtest(bot, BDD))
bot.add_command(mute)

@bot.event
async def on_message(msg):
	global muted
	server = msg.server
	author = msg.author
	if muted.get(server.id) is None:
		muted[server.id] = dict()
	if muted[server.id].get(author.id) is not None:
		etime = muted[server.id][author.id][0].get_elapsed_time_s()
		mtime = muted[server.id][author.id][1]
		if etime >= mtime:
			del muted[server.id][author.id]
			await bot.process_commands(msg)
			return
		else:
			await bot.delete_message(msg)
			return
	else:
		await bot.process_commands(msg)

@bot.event
async def on_ready():
	print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))

bot.run('Mzc1NzQ5OTgxNTIyNjI0NTMz.DRW08w.CxyPE9_bNQp0OP2SBukNtnzZb3o')
