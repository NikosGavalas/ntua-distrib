
import socket
import sys
import signal
import argparse

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
			lg.error('port binding failure')

		#if not USE_SEQUENCER:
		#	self.socket.setblocking(False)

	def getSocket(self):
		return self.socket
	
	def __enter__(self):
		return self.socket

	def __exit__(self, exc_type, exc_val, traceback):
		self.socket.close()

class Sequencer:
	def __init__(self, address, username):
		self.address = address
		self.username = username

		self.uid = 0

		self.groups = Groups()
		self.members = Members()

		self.selectedGroup = None

		self.counter = 0

		server = UDPServer(self.address)
		self.sock = server.getSocket()

		lg.debug('client listening on %s:%s' % self.address)

	def listen(self):
		while True:
			data, addr = self.sock.recvfrom(4096)

			if not data:
				continue

			self.onReceive(data.decode())

	def multicastInGroup(self, group, typ, message, origin):
		if typ == msg.MessageType.Application:
			self.counter = self.counter + 1

		for member in group.getMembers():
			self.unicastInGroup(group, member, typ, message, self.counter, origin)

	def unicastInGroup(self, group, member, typ, content, counter, origin):
		message = msg.Message(typ,
		                      group.getName(),
		                      self.username,
		                      content,
		                      self.address[0],
		                      self.address[1],
		                      counter,
							  origin)
		
		text = str(message)

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			lg.debug('sending %s to %s' % (text, member.getAddress()))
			sock.sendto(text.encode(), member.getAddress())

	""" Returns true if message has been delivered to the application layer """
	def onReceive(self, text):
		message = msg.Message.fromString(text)
		lg.debug('received %s from %s' % (message, message.getSrcAddress()))

		group = self.groups.getGroupByName(message.getGroupName())
		
		""" If the group doesn't exist, then the message is not for us, so we return """
		if group is None:
			group = Group(message.getGroupName())
			self.groups.addNewGroup(group)

		sender = self.members.getMemberByUsername(message.getUsername())

		""" If we don't already know the sender, we append him in our structs """
		if sender is None:
			sender = Member(message.getSrcAddress(), message.getUsername())
			self.members.addNewMember(sender)
			group.addMember(sender)

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
				self.forwardMessage(message.getGroupName(),
				                    message.getOrigin(),
				                    message.getContent())

				return True

			"""FIFO logic here. We assume that when a client joins a group,
			the initial value of the counter for his peer's messages is set 
			to the first value he receives"""
			if message.getCounter() == sender.getCounterForGroup(group) + 1:
				# Accept the message
				sender.incrementCounterForGroup(group)
				self.forwardMessage(message.getGroupName(),
				                    message.getOrigin(),
				                    message.getContent())

				return True
			
			else:
				lg.debug('buffering message, counter is %s, sender has %s' % (message.getCounter(), sender.getCounterForGroup(group)))

		return False

	def forwardMessage(self, groupname, origin, content):
		group = self.groups.getGroupByName(groupname)
		self.multicastInGroup(group, msg.MessageType.Application, content, origin)

	def quit(self):
		self.sock.close()


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('addr', help="the sequencer's address in the \
	                     form of host:port (e.g. 123.123.123.123:12345)")
	parser.add_argument('-v', help='verbose output (use for debugging)', action='store_true', default=False)
	args = parser.parse_args()

	addr = args.addr.split(':')
	SEQUENCER_ADDR = (addr[0], int(addr[1]))

	if args.v:
		lg.setDEBUG()

	username = 'sequencer'

	client = Sequencer(SEQUENCER_ADDR, username)

	def sig_handler(sig, frame):
		print('\nbye')
		client.quit()
		sys.exit(0)

	signal.signal(signal.SIGINT, sig_handler)

	lg.info('Sequencer instance started:\n \
                           IP: %s\n \
                           Port: %s\n \
                           Username: %s\n' \
	% (SEQUENCER_ADDR[0], int(SEQUENCER_ADDR[1]), username))

	client.listen()
