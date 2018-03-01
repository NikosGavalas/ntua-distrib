
import socket
import sys
import signal
from select import select

from config import *
import logger as lg
import message as msg
from peers import *


class UDPServer:
	def __init__(self, ip, port):
		self.ip = ip
		self.port = port

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		try:
			self.socket.bind((self.ip, self.port))
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
	def __init__(self, ip, port, username):
		self.ip = ip
		self.port = port
		self.username = username

		self.uid = self.register()

		self.groups = [] # <- can be a seperate class, too many functions

		self.selectedGroup = None

		server = UDPServer(self.ip, self.port)
		self.sock = server.getSocket()
		lg.debug('client listening on %s:%s' % (self.ip, str(self.port)))

	def prompt(self):
		print('[%s]> ' % (username), end='', flush=True)
		
	def listen(self):
		while True:
			self.prompt()

			streams = [self.sock, sys.stdin]
			inp, _, _ = select(streams, [], [])

			for stream in inp:
				if stream == self.sock:
					data, addr = self.sock.recvfrom(4096)

					if not data:
						continue

					self.onReceive(data.decode())

				elif stream == sys.stdin:
					self.onText(sys.stdin.readline())

	def onText(self, inp):
		if inp.startswith('!'):

			if inp.startswith('!lg'):
				groups = client.listGroups()
				print('groups: %s' % (groups))
				return

			if inp.startswith('!lm'):
				try:
					group = inp.split()[1]
				except IndexError:
					print('usage: !lm <group>')
					return

				members = client.listMembers(group)
				print('members in "%s": %s' % (group, members))
				return

			if inp.startswith('!j'):
				try:
					group = inp.split()[1]
				except IndexError:
					print('usage: !j <group>')
					return

				client.joinGroup(group)
				print('joining group %s' % (group))
				return

			if inp.startswith('!w'):
				try:
					group = inp.split()[1]
				except IndexError:
					print('usage: !w <group>')
					return
				
				client.selectGroup(group)
				print('writting in group %s' % (group))
				return

			if inp.startswith('!e'):
				try:
					group = inp.split()[1]
				except IndexError:
					print('usage: !e <group>')
					return

				client.exitGroup(group)
				print('leaving group %s' % (group))
				return

			if inp.startswith('!q'):
				print('quitting...')
				client.quit()
				sys.exit(0)

			#TODO list groups where current user belongs to
			#elif inp.startswith('!mg'):

			#elif inp.startswith('!h'):
			#	help?
			
			print('invalid ui command')
			return

		# Else if input doesnt not start with '!':
		else:
			client.multicast(inp)
		
		return

	def multicast(self, message):
		if self.selectedGroup is None:
			print('you need to select a group first')
			return

		for member in self.selectedGroup.getMembers():
			self.unicast(member, message)

	def unicast(self, member, message):
		forged = msg.forgeMessage(self.selectedGroup.name, 
									self.username, message,
									self.ip,
									self.port)
		
		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			lg.debug('sending %s to %s:%s' % (forged, member.getIp(), member.getPort()))
			sock.sendto(forged.encode(), (member.getIp(), member.getPort()))

	def onReceive(self, message):
		groupname, username, content, srcIp, srcPort = msg.parseMessage(message)
		lg.debug('received %s from %s:%s' % (message, srcIp, str(srcPort)))

		group = self.getGroupByName(groupname)

		members = [member.getUsername() for member in group.getMembers()]

		if username not in members:
			group.addMember(Member(srcIp, srcPort, username))

		## Add fifo logic here

		print('\nin %s %s says:: %s' % (group, username, content))

	def askTracker(self, message):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			try:
				sock.connect((TRACKER_IP, TRACKER_PORT))
			except ConnectionRefusedError:
				lg.error('connection with tracker refused')
				sys.exit(1)

			lg.debug('asking tracker: %s' % (message))

			sock.send(message.encode())

			reply_raw = sock.recv(4096)
			reply = reply_raw.decode()

			lg.debug('tracker reply: %s' % (reply))

			sock.close()

			return reply

	def register(self):
		cont = {'Ip': self.ip, 'Port': self.port, 'Username': self.username}
		req = msg.forgeRequest(msg.RequestType['Register'], cont)

		status, content = msg.parseReply(self.askTracker(req))

		return content

	def listGroups(self):
		req = msg.forgeRequest(msg.RequestType['ListGroups'], '')

		status, content = msg.parseReply(self.askTracker(req))

		return content

	def listMembers(self, group):
		cont = {'Group': group}
		req = msg.forgeRequest(msg.RequestType['ListMembers'], cont)

		status, content = msg.parseReply(self.askTracker(req))

		return [peer['Username'] for peer in content]

	def joinGroup(self, groupname):
		cont = {'Id': self.uid, 'Group': groupname}
		req = msg.forgeRequest(msg.RequestType['JoinGroup'], cont)

		status, content = msg.parseReply(self.askTracker(req))
		
		group = self.getGroupByName(groupname)

		if group is None:
			group = Group(groupname)
			self.groups.append(group)

		group.clearMembers()

		for peer in content:
			mem = Member(peer['Ip'], peer['Port'], peer['Username'])
			group.addMember(mem)

	def selectGroup(self, group):
		self.selectedGroup = self.getGroupByName(group)

	# the following method is used by the class tracker too
	# TODO: DNRY
	def getGroupByName(self, groupname):
		for group in self.groups:
			if group.getName() == groupname:
				return group
		return None

	def exitGroup(self, group):
		cont = {'Id': self.uid, 'Group': group}
		req = msg.forgeRequest(msg.RequestType['ExitGroup'], cont)

		status, content = msg.parseReply(self.askTracker(req))

	def quit(self):
		cont = {'Id': self.uid}
		req = msg.forgeRequest(msg.RequestType['Quit'], cont)

		status, content = msg.parseReply(self.askTracker(req))

		self.sock.close()


if __name__ == '__main__':

	def parseArgs(args):
		if len(args) < 4:
			lg.fatal('incorrect arguments')
			sys.exit(1)

		return (args[1], int(args[2]), args[3])

	ip, port, username = parseArgs(sys.argv)

	client = Client(ip, port, username)

	def sig_handler(sig, frame):
		lg.info('exiting...')
		client.quit()
		sys.exit(0)

	signal.signal(signal.SIGINT, sig_handler)

	lg.info('Client instance started\n \
	IP: %s\n \
	Port: %s\n \
	Username: %s\n' \
	% (ip, port, username))

	client.listen()
