
import socket
import sys
import signal
from config import *
import logger as lg
import message as msg

from peers import *


def sig_handler(sig, frame):
	lg.info('exiting...')
	sys.exit(0)

signal.signal(signal.SIGINT, sig_handler)

class Client:
	def __init__(self, ip, port, username):
		self.ip = ip
		self.port = port
		self.username = username

		self.uid = self.register()

		self.groups = []

	def askTracker(self, message):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			try:
				sock.connect((TRACKER_IP, TRACKER_PORT))
			except ConnectionRefusedError:
				lg.error('connection with tracker refused')
				sys.exit()

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

	def joinGroup(self, group):
		cont = {'Id': self.uid, 'Group': group}
		req = msg.forgeRequest(msg.RequestType['JoinGroup'], cont)

		status, content = msg.parseReply(self.askTracker(req))
		
		newGroup = Group(group)

		for peer in content:
			newGroup.addMember(Member(peer['Ip'], peer['Port'], peer['Username']))
		
		self.groups.append(newGroup)


def parseArgs(args):
	if len(args) < 4:
		lg.fatal('incorrect arguments')
		sys.exit(1)

	return (args[1], args[2], args[3])


if __name__ == '__main__':

	ip, port, username = parseArgs(sys.argv)

	client = Client(ip, port, username)

	lg.info('Client instance started\n \
	IP: %s\n \
	Port: %s\n \
	Username: %s\n' \
	% (ip, port, username))
	
	while True:
		inp = input('\n[%s]> ' % (username))
		
		if inp.startswith('!lg'):
			groups = client.listGroups()
			print('groups: %s' % (groups))
		
		elif inp.startswith('!lm'):
			try:
				group = inp.split()[1]
			except IndexError:
				print('usage: !lm <group>')
				continue

			members = client.listMembers(group)
			print('members in "%s": %s' % (group, members))

		elif inp.startswith('!j'):
			try:
				group = inp.split()[1]
			except IndexError:
				print('usage: !j <group>')
				continue

			client.joinGroup(group)
			print('joining group %s' % (group))

		elif inp.startswith('!w'): # leave last
			print('ok')

		elif inp.startswith('!e'): # TODO
			print('ok')

		elif inp.startswith('!q'): # TODO
			print('ok')

		#elif inp.startswith('!h'):
		#	help?

		else:
			print('invalid ui command')
