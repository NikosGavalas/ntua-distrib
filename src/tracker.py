
import socket
import threading
import signal
import sys

from config import *
import logger as lg
import message as msg
from peers import Member, Group

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

	def getSocket(self):
		return self.socket

	def __enter__(self):
		return self.socket

	def __exit__(self, exc_type, exc_val, traceback):
		self.socket.close()


class Tracker:
	def __init__(self, ip, port, backlog):
		self.ip = ip
		self.port = port
		self.backlog = backlog
		
		self.groups = []
		self.members = []

		server = TCPServer(self.ip, self.port, self.backlog)
		self.sock = server.getSocket()
		lg.info('tracker listening on %s:%s' % (self.ip, str(self.port)))

	def serve(self):
		while True:
			clientSock, clientAddr = self.sock.accept()
			lg.debug('connection accepted from ' + clientAddr[0] + ':' + str(clientAddr[1]))

			thread = threading.Thread(target=self.handleRequest, args=(clientSock, clientAddr, ))

			thread.start()
			#thread.join()

	def exit(self):
		self.sock.close()

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
			groupname = reqContent['Group']

			group = self.getGroupByName(groupname)
				
			ret = [member.toDict() for member in group.getMembers()] if group is not None else []

			return msg.forgeReply(True, ret)


		if reqType == msg.RequestType['JoinGroup']:
			uid = reqContent['Id']
			groupname = reqContent['Group']

			member = self.getMemberById(uid)
			group = self.getGroupByName(groupname)

			if group is None:
				group = Group(groupname)
				self.groups.append(group)

			if member not in group.getMembers():
				group.addMember(member)

			return msg.forgeReply(True, [member.toDict() for member in group.getMembers()]) # TODO: exact code is above, group 'em
		
		if reqType == msg.RequestType['ExitGroup']:
			uid = reqContent['Id']
			groupname = reqContent['Group']

			member = self.getMemberById(uid)

			self.getGroupByName(groupname).removeMember(member)

			return msg.forgeReply(True, '')

		if reqType == msg.RequestType['Quit']:
			uid = reqContent['Id']

			member = self.getMemberById(uid)

			# remove member from all groups
			for group in self.groups:
				try:
					group.removeMember(member)
				except ValueError:
					pass
				
			del member

			return msg.forgeReply(True, '')

		return msg.forgeReply(False, '')

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

	def getGroupByName(self, groupname):
		for group in self.groups:
			if group.getName() == groupname:
				return group
		return None


if __name__ == '__main__':
	tracker = Tracker(TRACKER_IP, TRACKER_PORT, TRACKER_BACKLOG)

	def sig_handler(sig, frame):
		lg.info('exiting...')
		tracker.exit()
		sys.exit(0)

	signal.signal(signal.SIGINT, sig_handler)

	tracker.serve()
