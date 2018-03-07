
import socket
import sys
import signal
from select import select

from config import *
import logger as lg
import message as msg
from peers import Member, Group, Groups, Members


class UDPServer:
	def __init__(self, address):
		self.address = address

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		try:
			self.socket.bind(self.address)
		except socket.error:
			lg.error('port binding failure')

		self.socket.setblocking(False)

	def getSocket(self):
		return self.socket
	
	def __enter__(self):
		return self.socket

	def __exit__(self, exc_type, exc_val, traceback):
		self.socket.close()


class Client:
	def __init__(self, address, username):
		self.address = address
		self.username = username

		self.uid = self.register()

		self.groups = Groups()
		self.members = Members()

		self.selectedGroup = None

		server = UDPServer(self.address)
		self.sock = server.getSocket()

		lg.debug('client listening on %s:%s' % self.address)

	def prompt(self):
		print('[%s]> ' % (username), end='', flush=True)
		
	def listen(self):
		self.prompt()
		
		while True:

			# Unix select syscall
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

			#TODO list groups where current user belongs to
			#elif inp.startswith('!mg'):

			#elif inp.startswith('!h'):
			#	help?
			
			print('invalid ui command')
			return

		# Else if input doesnt not start with '!':
		else:
			if inp == '\n':
				return

			self.multicast(msg.MessageType["Application"], inp.strip("\n"))

	def multicast(self, typ, message):
		if self.selectedGroup is None:
			print('you need to select a group first')
			return

		for member in self.selectedGroup.getMembers():
			self.unicast(member, typ, message)

	def unicast(self, member, typ, content):
		message = msg.Message(typ,
							self.selectedGroup.name, 
							self.username, 
							content,
							self.address[0],
							self.address[1])
		
		text = str(message)

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			lg.debug('sending %s to %s' % (text, member.getAddress()))
			sock.sendto(text.encode(), member.getAddress())

	def onReceive(self, text):
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
			newMem = Member(message.getSrcAddress(), message.getUsername())
			self.members.addNewMember(newMem)
			group.addMember(newMem)

		messageType = message.getType()

		if messageType == msg.MessageType['Bye']:
			group.removeMember(sender)
			return False
		
		elif messageType == msg.MessageType['Hello']:
			return False

		elif messageType == msg.MessageType['Application']:

			## Add fifo logic here

			self.deliverApplicationMessage(message.getGroupName(),
											message.getUsername(),
											message.getContent())
		
			return True

		return False

	def deliverApplicationMessage(self, groupname, username, content):
		print('\nin %s %s says:: %s' % (groupname, username, content))

	def askTracker(self, message):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			try:
				sock.connect(TRACKER_ADDR)
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

		req = msg.Request(msg.RequestType['Register'], cont)

		reply = msg.Reply.fromString(self.askTracker(req))

		return reply.getContent()

	def listGroups(self):
		cont = {}

		req = msg.Request(msg.RequestType['ListGroups'], cont)

		reply = msg.Reply.fromString(self.askTracker(req))

		return reply.getContent()

	def listMembers(self, group):
		cont = {'Group': group}

		req = msg.Request(msg.RequestType['ListMembers'], cont)

		reply = msg.Reply.fromString(self.askTracker(req))

		return [peer['Username'] for peer in reply.getContent()]

	def joinGroup(self, groupname):
		cont = {'Username': self.username, 
				'Group': groupname}

		req = msg.Request(msg.RequestType['JoinGroup'], cont) 

		reply = msg.Reply.fromString(self.askTracker(req))
		
		group = self.groups.getGroupByName(groupname)

		if group is None:
			group = Group(groupname)
			self.groups.addNewGroup(group) 

		group.clearMembers()

		for peer in reply.getContent():
			mem = Member((peer['Ip'], int(peer['Port'])), peer['Username'])
			self.members.addNewMember(mem) # it is bad that I have to add him in two places though
			group.addMember(mem)
			
			"""Send Hello message"""
			self.unicast(mem, msg.MessageType['Hello'], '')			

	def selectGroup(self, groupname):
		self.selectedGroup = self.groups.getGroupByName(groupname)

	def exitGroup(self, groupname):
		cont = {'Username': self.username, 
            	'Group': groupname}

		req = msg.Request(msg.RequestType['ExitGroup'], cont)

		_ = msg.Reply.fromString(self.askTracker(req))

		self.multicast(msg.MessageType['Bye'], '')

		self.groups.removeGroupByName(groupname)
		self.selectedGroup = None

	def quit(self):
		cont = {'Username': self.username}

		req = msg.Request(msg.RequestType['Quit'], cont)

		_ = msg.Reply.fromString(self.askTracker(req))

		self.sock.close()


if __name__ == '__main__':

	def parseArgs(args):
		if len(args) < 4:
			lg.fatal('incorrect arguments')
			sys.exit(1)

		return (args[1], int(args[2]), args[3])

	ip, port, username = parseArgs(sys.argv)
	addr = (ip, port)

	client = Client(addr, username)

	def sig_handler(sig, frame):
		print('\nbye')
		client.quit()
		sys.exit(0)

	signal.signal(signal.SIGINT, sig_handler)

	lg.info('Client instance started\n \
	IP: %s\n \
	Port: %s\n \
	Username: %s\n' \
	% (ip, port, username))

	client.listen()
