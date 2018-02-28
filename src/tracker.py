
import socket
import threading
import signal
import sys

from config import *
import logger as lg
import message as msg
from peers import Member, Group


def sig_handler(sig, frame):
	lg.info('exiting...')
	sys.exit(0)

signal.signal(signal.SIGINT, sig_handler)


class TCPServer:
	def __init__(self, ip, port, backlog):
		self.ip = ip
		self.port = port
		self.backlog = backlog

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.socket.bind((self.ip, self.port))
		except socket.error:
			lg.error('port binding failure')

		self.socket.listen(self.backlog)
		lg.debug('tracker listening on port ' + str(self.port))

	def __enter__(self):
		return self.socket

	def __exit__(self, exc_type, exc_val, traceback):
		self.socket.close()


class Tracker:
	def __init__(self, ip, port, backlog):
		self.ip = ip
		self.port = port
		self.backlog = backlog
		
		self.groups = [Group('asdf'), Group('qwer')]
		self.members = []

	def serve(self):
		with TCPServer(self.ip, self.port, self.backlog) as sock:
			while True:
				clientSock, clientAddr = sock.accept()
				lg.debug('connection accepted from ' + clientAddr[0] + ':' + str(clientAddr[1]))

				thread = threading.Thread(target=self.handleRequest, args=(clientSock, clientAddr, ))

				thread.start()
				#thread.join()

	def handleRequest(self, conn, addr):
		data = conn.recv(4096)
		
		if data:
			message = data.decode()

			lg.debug('received from %s:%s message: %s' % (addr[0], str(addr[1]), message))

			reply = self.answer(message)

			lg.debug('replying to %s:%s with: %s' % (addr[0], str(addr[1]), reply))

			reply_raw = reply.encode()
			conn.sendall(reply_raw)
			
		conn.close()

	def answer(self, message):
		reqType, reqContent = msg.parseRequest(message)

		if reqType == msg.RequestType['Register']:
			ip = reqContent['Ip']
			port = reqContent['Port']
			username = reqContent['Username']
			
			newMem = Member(ip, port, username)
			uid = newMem.getUid()

			self.members.append(newMem)

			return msg.forgeReply(True, uid)

		if reqType == msg.RequestType['ListGroups']:
			return msg.forgeReply(True, [str(group) for group in self.groups])

		if reqType == msg.RequestType['ListMembers']:
			group = reqContent['Group']

			idx = self.getIndexGroup(group)

			ret = self.groups[idx].getMembers()

			return msg.forgeReply(True, [member.toDict() for member in ret])

		if reqType == msg.RequestType['JoinGroup']:
			uid = reqContent['Id']
			group = reqContent['Group']

			member = self.getMemberById(uid)

			idx = self.getIndexGroup(group) # <-- maybe turn this function into getGroupByName?

			if idx >= 0:
				self.groups[idx].addMember(member)
			else:
				newGroup = Group(group)
				newGroup.addMember(member)
				self.groups.append(newGroup)

			return msg.forgeReply(True, [member.toDict() for member in self.groups[idx].getMembers()]) # <-- TODO: exact code is above, use a func
		
		# return 'you fucked up'

	def getMemberById(self, uid):
		for member in self.members:
			if member.uid == uid:
				return member
		return None

	def getIndexGroup(self, targetGroup): # <-- there is a built-in class for this, I think index but whatev
		for idx, group in enumerate(self.groups):
			if group.name == targetGroup:
				return idx
		return -1


if __name__ == '__main__':
	tracker = Tracker(TRACKER_IP, TRACKER_PORT, TRACKER_BACKLOG)

	tracker.serve()
