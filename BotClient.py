#!/usr/bin/python
import httplib, urllib, json, time, threading

class BotClient():

	def __init__(self):
		self.version = '<your bot name here> v0.1 running on <platform>'
		self.Token = "<your bot token here>"
		self.BaseUri = "api.telegram.org"
		self.Path = '/bot' + self.Token + '/{0}'
		self.connection = httplib.HTTPSConnection(self.BaseUri)
		self._dispatch = Dispatch(self._send_message, self.version)
		self.mailbox = Mailbox()
		self.me = ''
		self.echo_mode = False

	def Test(self):
		response = self._send_request('getMe')
		if not self._response_is_valid(response):
			print '>> ERROR: Cannot read response.'
			self._print_json_object(response)
			return

		result = response['result']
		self._dispatch.me = '{0} (#{1})'.format(result['username'], result["id"])
		print '>> {0} is alive! [#{1}]'.format(result['first_name'], result['id'])
		
	def RunOnce(self):
		updates = self._get_updates()
		last_update = 0
		for update in updates:
			try:
				self._handle_update(update)
			except:
				print '>> ERROR: {0}'.format(update)

			last_update = update['update_id']

		print '>> last_update: {0}'.format(last_update)

	def RunLoop(self):
		last_update = 0

		while True:
			updates = self._get_updates(last_update + 1)
			for update in updates:
				try:
					self._handle_update(update)
				except :
					print '>> ERROR: {0}'.format(update)
				last_update = update['update_id']
				time.sleep(0.5)

	def _get_updates(self, offset = None):
		params = None
		if offset is not None:
			params = {'offset' : offset, 'limit' : 10}
		response = self._send_request('getUpdates',params)
		if not self._response_is_valid(response):
			print '>> ERROR: invalid response'
			self._print_json_object(response)
			return
		
		if len(response['result']) > 0:
			print '>> got [{0}] updates'.format(len(response['result']))
		return response['result']

	def _send_message(self, chat_id, text):
		if chat_id is None:
			return None
		params = {'chat_id' : chat_id, 'text' : text}
		response = self._send_request('sendMessage', params)
		if not self._response_is_valid(response):
			print '>> ERROR: invalid response'
			self._print_json_object(response)
			return None

	def _handle_update(self, update):
		
		u = BotUpdate(update)
		if u is None or not update.has_key('message'):
			print '>> ERROR: cannot read update, skipping'
			return None

		print '>> update [#{0}]: {1} (@{2})'.format(u.update_id, u.text, u.user)
		command = u.text.lower()
		
		if self.echo_mode:
			self._send_message(u.chat_id, "you said: " + u.text)

		if not self._dispatch.handle(command, u):
			self._local_dispatch(command, u)

	def _local_dispatch(self, command, u):
		
		if command.startswith('echo mode'):
			parts = u.text.split(' ')
			if len(parts) > 2 and parts[2] in ['on','off']:
				self._send_message(u.chat_id, 'ok.')
				if parts[2] == 'on':
					self.echo_mode = True
				else:
					self.echo_mode = False

		else:
			self._send_message(u.chat_id, "Say what?") # "I don't know what you're talking about.")

	def _send_request(self, method, params=None):
		query = ''
		if params is not None:
			query = '?' + urllib.urlencode(params)
		
		#print '[DEBUG] Request: ' + self.Path.format(method) + query

		self.connection.request('GET',self.Path.format(method) + query)
		res = self.connection.getresponse()
		
		data = res.read()
		if res.status is not 200:
			self._handle_error(data)
			return
		return json.loads(data)

	def _response_is_valid(self, res):
		return res is not None and res.has_key('ok') and res['ok'] is True and res.has_key('result')

	def _handle_error(self,err_string):
		print err_string

	def _print_json_object(self, obj):
		print json.dumps(obj, indent = 4, separators = (',', ': '))

	def _print_json_from_string(self, string):
		obj = json.loads(string)
		self_._print_json_object(obj)


class Dispatch():

	def __init__(self, send_method, version):
		self.dispatch = {}
		self._send_message = send_method
		self.sw_version = version
		self._init_hw()
		self._initialize()
		self.state = 0
		self.me = ''

	def handle(self, command, update):
		if not self.dispatch.has_key(command):
			return False
		#print '[DEBUG] running:', command, update
		func = self.dispatch[command]
		func(update)
		return True

	def _initialize(self):
		self.dispatch['hi'] = self.hello
		self.dispatch['hello'] = self.hello
		self.dispatch['/start'] = self.start
		self.dispatch['version'] = self.version
		self.dispatch['who am i?'] = self.who
		self.dispatch['chat info'] = self.chat_info
		self.dispatch['blink'] = self.blink
		self.dispatch['led on'] = self.led_on
		self.dispatch['led off'] = self.led_off
		self.dispatch['help'] = self.help
		self.dispatch['cpu temp'] = self.cpu_temp
		self.dispatch['who are you?'] = self.who_are_you
		
	def _init_hw(self):
		self.led = Led(17)
		self.pi = PiZero()

	def hello(self, u):
		self._send_message(u.chat_id, "Hello to you too, {0}".format(u.user))

	def start(self, u):
		self._send_message(u.chat_id, "Hi, i'm " + self.sw_version + ". type 'help' to get the command list.")

	def version(self, u):
		self._send_message(u.chat_id, self.sw_version)
				
	def who(self, u):
		self._send_message(u.chat_id, "you're @{0}, (#{1})".format(u.user, u.user_id))

	def chat_info(self, u):
		self._send_message(u.chat_id, "chat #{0}, {1}".format(u.chat_id, u.chat_type))

	def blink(self, u):
		self._send_message(u.chat_id, "let's do this!")
		self.led.blink()

	def led_on(self, u):
		self._send_message(u.chat_id, "sure. it's on.")
		self.led.on()

	def led_off(self, u):
		self._send_message(u.chat_id, "sure. it's off.")
		self.led.off()

	def cpu_temp(self, u):
		self._send_message(u.chat_id, self.pi.read_cpu_temp())

	def help(self, u):
		commands = self.dispatch.keys()
		commands.sort()
		self._send_message(u.chat_id, "available commands:\n > " + '\n > '.join(commands))

	def who_are_you(self, u):
		self._send_message(u.chat_id, "I'm " + self.me)

class BotUpdate():

	def __init__(self, update):
		if update.has_key('update_id'):
			self.update_id = update['update_id']

		if not update.has_key('message'):
			return

		if update['message'].has_key('text'):
			self.text = update['message']['text']
		else:
			self.text = ''
		
		if update['message'].has_key('from'):
			if update['message']['from'].has_key('first_name'):
				self.user = update['message']['from']['first_name']
			if update['message']['from'].has_key('last_name'):
				self.user = self.user + '_' + update['message']['from']['last_name']
			if update['message']['from'].has_key('id'):
				self.user_id = update['message']['from']['id']
		
		if update['message'].has_key('chat'):
			if update['message']['chat'].has_key('id'):
				self.chat_id = update['message']['chat']['id']
			if update['message']['chat'].has_key('type'):
				self.chat_type = update['message']['chat']['type']		
		
		if update['message'].has_key('date'):
			self.date = update['message']['date']

class Led():

	def __init__(self, gpio):
		self.gpio = gpio
		self.led = None
		self.period = 0.25
		self.e = threading.Event()
		self._setup()

	def _setup(self):
		try:
			from gpiozero import LED
			self.led = LED(17)
		except:
			print '[Cannot import LED from gpiozero]'

	def off(self):
		if self.led is None:
			return
		self.e.set()
		time.sleep(2*self.period)
		self.led.on()

	def on(self):
		if self.led is None:
			return
		self.e.set()
		time.sleep(2*self.period)
		self.led.off()

	def blink(self):
		self.e.clear()
		self.t = threading.Thread(name='non-block', target=self._flash, args=(self.e,self.period))
		self.t.start()

	def _flash(self,e,period):
		if self.led is None:
			return
		while not e.isSet():
			time.sleep(period/2)
			self.led.on()
			time.sleep(period/2)
			self.led.off()

class PiZero():

	def __init__(self):
		self.cpu = None
		self._setup()

	def _setup(self):
		try:
			from gpiozero import CPUTemperature
			self.cpu = CPUTemperature(min_temp=50, max_temp=90)
		except:
			print '[Cannot import CPUTemperature from gpiozero]'

	def read_cpu_temp(self):
		if self.cpu is not None:
			return '{}C'.format(self.cpu.temperature)
		else:
			return 'cannot read cpu temperature.'

