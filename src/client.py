
import socket
import sys
import signal
import argparse
import time
from select import select

from logger import Logger
import message as msg
from peers import Member, Group, Groups, Members

lg = Logger()

class UDPServer:
	def __init__(self, address):
		self.address = address

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		try:
			self.socket.bind(self.address)
		except socket.error:
			lg.fatal('port binding failure')
			sys.exit(1)

		self.socket.setblocking(False)

	def getSocket(self):
		return self.socket
	
	def __enter__(self):
		return self.socket

	def __exit__(self, exc_type, exc_val, traceback):
		self.socket.close()


class Client:
	def __init__(self, address, username, tracker_addr, use_seq):
		self.address = address
		self.username = username
		self.TRACKER_ADDR = tracker_addr
		self.USE_SEQUENCER = use_seq

		self.uid = self.register()

		self.groups = Groups()
		self.members = Members()

		self.selectedGroup = None

		self.counter = 0

		server = UDPServer(self.address)
		self.sock = server.getSocket()

		lg.debug('client listening on %s:%s' % self.address)

	def prompt(self):
		print('[%s]> ' % (username), end='', flush=True)
		
	def listen(self):
		self.prompt()
		
		while True:

			""" Unix select syscall for efficient IO without threading """
			streams = [self.sock, sys.stdin]
			inp, _, _ = select(streams, [], [])

			for stream in inp:
				if stream == self.sock:
					data, addr = self.sock.recvfrom(4096)

					if not data:
						continue

					if self.onReceive(data.decode()):
						self.prompt()

				elif stream == sys.stdin:
					self.onText(sys.stdin.readline())
					self.prompt()

	def onText(self, inp):
		if inp.startswith('!'):

			if inp.startswith('!lg'):
				groups = self.listGroups()

				print('groups: %s' % (groups))
				return

			if inp.startswith('!lm'):
				try:
					group = inp.split()[1]
				except IndexError:
					print('usage: !lm <group>')
					return

				members = self.listMembers(group)
				print('members in "%s": %s' % (group, members))
				return

			if inp.startswith('!j'):
				try:
					groupname = inp.split()[1]
				except IndexError:
					print('usage: !j <group>')
					return

				self.joinGroup(groupname)
				print('joining group %s' % (groupname))
				return

			if inp.startswith('!w'):
				try:
					group = inp.split()[1]
				except IndexError:
					print('usage: !w <group>')
					return
				
				self.selectGroup(group)
				print('writting in group %s' % (group))
				return

			if inp.startswith('!e'):
				try:
					group = inp.split()[1]
				except IndexError:
					print('usage: !e <group>')
					return

				self.exitGroup(group)
				print('leaving group %s' % (group))
				return

			if inp.startswith('!q'):
				print('bye')
				self.quit()
				sys.exit(0)

			#TODO flush buffers
			#elif inp.startswith('!f'):

			#TODO list groups where current user belongs to
			#elif inp.startswith('!mg'):

			print('invalid ui command\nusage: !lg, !lm <group>, !j <group>, !w <group>, !e <group>, !q')
			return

		else:
			if inp == '\n':
				return

			if self.selectedGroup is None:
				print('you need to select a group first')
				return
			
			self.multicastInGroup(self.selectedGroup, msg.MessageType.Application, inp.strip("\n"))

	def multicastInGroup(self, group, typ, message):
		if typ == msg.MessageType.Application:
			self.counter = self.counter + 1

		for member in group.getMembers():
			self.unicastInGroup(group, member, typ, message, self.counter)

	def unicastInGroup(self, group, member, typ, content, counter):
		message = msg.Message(typ,
		                      group.getName(),
		                      self.username, 
		                      content,
		                      self.address[0],
		                      self.address[1],
		                      counter,
							  self.username)
		
		text = str(message)

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			lg.debug('sending %s to %s' % (text, member.getAddress()))
			sock.sendto(text.encode(), member.getAddress())

	"""Returns true if message has been delivered to the application layer"""
	def onReceive(self, text):
		recv_time = time.time()
		lg.profile('message received at %f' % recv_time)

		message = msg.Message.fromString(text)
		lg.debug('received %s from %s' % (message, message.getSrcAddress()))

		group = self.groups.getGroupByName(message.getGroupName())
		
		"""If the group doesn't exist, then the message is not for us, so we return"""
		if group is None:
			return False

		sender = self.members.getMemberByUsername(message.getUsername())

		"""If we don't already know the sender, we append him in our structs
		(this was before adding the "hello" and "bye" messages)"""
		if sender is None:
			sender = Member(message.getSrcAddress(), message.getUsername())
			self.members.addNewMember(sender)
			group.addMember(sender)

		if self.USE_SEQUENCER and not sender.isSequencer():
			return False

		messageType = message.getType()

		if messageType == msg.MessageType.Bye:
			group.removeMember(sender)
			sender.resetCounterForGroup(group)
			return False
		
		elif messageType == msg.MessageType.Hello:
			group.addMember(sender)
			sender.initializeCounterForGroup(message.getCounter(), group)
			sender.incrementCounterForGroup(group)
			return False

		elif messageType == msg.MessageType.Application:

			if group.getCounter() == 0:
				sender.initializeCounterForGroup(message.getCounter(), group)

				sender.incrementCounterForGroup(group)
				self.deliverApplicationMessage(message.getGroupName(),
				                               message.getOrigin(),
				                               message.getContent())

				return True

			"""FIFO logic here. We assume that when a client joins a group,
			the initial value of the counter for his peer's messages is set 
			to the first value he receives"""
			if message.getCounter() == sender.getCounterForGroup(group) + 1:
				# Accept the message
				sender.incrementCounterForGroup(group)
				self.deliverApplicationMessage(message.getGroupName(),
				                               message.getOrigin(),
				                               message.getContent())

				#debuff = sender.tryDebuffMessage()
				#while debuff is not None:
				#	debuff = sender.tryDebuffMessage()
		
				return True
			
			else:
				lg.debug('buffering message, counter is %s, sender has %s' % (message.getCounter(), sender.getCounterForGroup(group)))
				#sender.bufferMessage(message)

		return False

	def deliverApplicationMessage(self, groupname, username, content):
		print('\nin %s %s says:: %s' % (groupname, username, content))

	def askTracker(self, message):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			try:
				sock.connect(self.TRACKER_ADDR)
			except ConnectionRefusedError:
				lg.error('connection with tracker refused')
				sys.exit(1)

			lg.debug('asking tracker: %s' % (message))

			sock.send(str(message).encode())

			reply_raw = sock.recv(4096)
			reply = reply_raw.decode()

			lg.debug('tracker reply: %s' % (reply))

			sock.close()

			return reply

	def register(self):
		cont = {'Ip': self.address[0], 
		        'Port': self.address[1], 
		        'Username': self.username}

		req = msg.Request(msg.RequestType.Register, cont)

		reply = msg.Reply.fromString(self.askTracker(req))

		return reply.getContent()

	def listGroups(self):
		cont = {}

		req = msg.Request(msg.RequestType.ListGroups, cont)

		reply = msg.Reply.fromString(self.askTracker(req))

		return reply.getContent()

	def listMembers(self, group):
		cont = {'Group': group}

		req = msg.Request(msg.RequestType.ListMembers, cont)

		reply = msg.Reply.fromString(self.askTracker(req))

		return [peer['Username'] for peer in reply.getContent()]

	def joinGroup(self, groupname):
		cont = {'Username': self.username, 
		        'Group': groupname}

		req = msg.Request(msg.RequestType.JoinGroup, cont) 

		reply = msg.Reply.fromString(self.askTracker(req))
		
		group = self.groups.getGroupByName(groupname)

		if group is None:
			group = Group(groupname)
			self.groups.addNewGroup(group) 

		group.clearMembers()

		for peer in reply.getContent():
			mem = Member((peer['Ip'], int(peer['Port'])), peer['Username'])
			self.members.addNewMember(mem)
			group.addMember(mem)
			
			"""Send Hello message"""
			self.unicastInGroup(group, mem, msg.MessageType.Hello, '', group.getCounter())			

	def selectGroup(self, groupname):
		self.selectedGroup = self.groups.getGroupByName(groupname)

	def exitGroup(self, groupname):
		group = self.groups.getGroupByName(groupname)
		
		if group is None:
			print("well you don't belong in that group anyway")
			return

		cont = {'Username': self.username, 
            	'Group': groupname}
		req = msg.Request(msg.RequestType.ExitGroup, cont)

		_ = msg.Reply.fromString(self.askTracker(req))

		for member in group.getMembers():
			member.resetCounterForGroup(group)

		self.multicastInGroup(group, msg.MessageType.Bye, '')

		if self.selectedGroup == group:
			self.selectedGroup = None

		self.groups.removeGroup(group)

	def quit(self):
		cont = {'Username': self.username}

		req = msg.Request(msg.RequestType.Quit, cont)

		_ = msg.Reply.fromString(self.askTracker(req))

		self.sock.close()


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('addr', help="the client's address in the \
	                     form of host:port (e.g. 123.123.123.123:12345)")
	parser.add_argument('name', help='username')
	parser.add_argument('tracker_addr', help="the tracker's address in the \
						form of host:port (e.g. 123.123.123.123:12345)")
	parser.add_argument('-t', help='execute tests (emulation mode) - provide file', action='store')
	parser.add_argument('-s', help="use sequencer for total ordering", action='store_true', default=False)
	parser.add_argument('-v', help='verbose output (use for debugging)', action='store_true', default=False)
	args = parser.parse_args()

	addr = args.addr.split(':')
	CLIENT_ADDR = (addr[0], int(addr[1]))

	username = args.name

	addr = args.tracker_addr.split(':')
	TRACKER_ADDR = (addr[0], int(addr[1]))

	USE_SEQUENCER = args.s
	if USE_SEQUENCER:
		lg.info('using sequencer')

	EXECUTE_TESTS = args.t is not None
	if EXECUTE_TESTS:
		filepath = args.t
		lg.setPROFILE()

	if args.v:
		lg.setDEBUG()
	
	client = Client(CLIENT_ADDR, username, TRACKER_ADDR, USE_SEQUENCER)

	def sig_handler(sig, frame):
		print('\nbye')
		client.quit()
		sys.exit(0)

	signal.signal(signal.SIGINT, sig_handler)

	lg.info('Client instance started\n \
                 IP: \t\t%s\n \
                 Port: \t%s\n \
                 Username: \t%s\n' \
                 % (CLIENT_ADDR[0], CLIENT_ADDR[1], username))

	if not EXECUTE_TESTS:
		client.listen()

	# if executing tests, read file, spam each line, and report time elapsed
	else:
		# give the listener to a background thread
		from threading import Thread
		t = Thread(target=client.listen)
		t.start()

		lg.info('spamming messages from file %s...' % (filepath))
		client.joinGroup('test')
		client.selectGroup('test')

		# wait for everyone to get ready
		time.sleep(5)

		start = time.time()

		with open(filepath) as f:
			for line in f:
				client.onText(line)

		end = time.time()
		elapsed = end - start

		# print the measurements
		time.sleep(5)
		print('start: %f' % (start))
		print('end: %f' % (end))
		print('elapsed: %f' % (elapsed))
