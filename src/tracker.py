
import socket
#import threading
import signal
import sys

from config import *
import logger as lg
import message as msg
from peers import Member, Group, Groups, Members

class TCPServer:
	def __init__(self, address, backlog):
		self.address = address
		self.backlog = backlog

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.socket.bind(self.address)
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
	def __init__(self, address, backlog):
		self.address = address
		self.backlog = backlog
		
		self.groups = Groups()

		self.members = Members()

		server = TCPServer(self.address, self.backlog)
		self.sock = server.getSocket()

		lg.info('tracker listening on %s:%s' % self.address)

	def serve(self):
		while True:
			clientSock, clientAddr = self.sock.accept()
			lg.debug('connection accepted from ' + clientAddr[0] + ':' + str(clientAddr[1]))

			self.handleRequest(clientSock, clientAddr)

			# thread = threading.Thread(target=self.handleRequest, args=(clientSock, clientAddr, ))

			# thread.start()
			#thread.join() # is this correct or threads never return?

	def exit(self):
		self.sock.close()

	def handleRequest(self, conn, addr):
		data = conn.recv(4096)
		
		if data:
			req = data.decode()

			lg.debug('received from %s:%s : %s' % (addr[0], str(addr[1]), req))

			reply = str(self.answer(req))

			lg.debug('replying to %s:%s with: %s' % (addr[0], str(addr[1]), reply))

			reply_raw = reply.encode()
			conn.sendall(reply_raw)
			
		conn.close()

	def answer(self, message):
		req = msg.Request.fromString(message)

		reqType = req.getType()
		reqContent = req.getContent()

		if reqType == msg.RequestType['Register']:
			ip = reqContent['Ip']
			port = reqContent['Port']
			username = reqContent['Username']
			
			member = self.members.getMemberByUsername(username)
			
			if member is None:
				member = Member((ip, port), username)
				self.members.addNewMember(member)

			uid = member.getUid()

			return msg.Reply(True, uid)

		if reqType == msg.RequestType['ListGroups']:
			return msg.Reply(True, self.groups.getGroupsSerializable())

		if reqType == msg.RequestType['ListMembers']:
			groupname = reqContent['Group']

			group = self.groups.getGroupByName(groupname)

			if group is None:
				return msg.Reply(False, [])

			return msg.Reply(True, group.getMembersSerializable())


		if reqType == msg.RequestType['JoinGroup']:
			username = reqContent['Username']
			groupname = reqContent['Group']

			member = self.members.getMemberByUsername(username)

			if member is None:
				return msg.Reply(False, [])
			
			group = self.groups.getGroupByName(groupname)

			if group is None:
				group = Group(groupname)
				self.groups.addNewGroup(group)

			group.addMember(member)

			return msg.Reply(True, group.getMembersSerializable())
		
		if reqType == msg.RequestType['ExitGroup']:
			username = reqContent['Username']
			groupname = reqContent['Group']

			member = self.members.getMemberByUsername(username)

			group = self.groups.getGroupByName(groupname)

			if group is not None:
				group.removeMember(member)

			return msg.Reply(True, '')

		if reqType == msg.RequestType['Quit']:
			username = reqContent['Username']

			member = self.members.getMemberByUsername(username)

			self.groups.removeMemberFromAllGroups(member)
				
			self.members.deleteMember(member)

			return msg.Reply(True, '')

		return msg.Reply(False, '')


if __name__ == '__main__':
	tracker = Tracker(TRACKER_ADDR, TRACKER_BACKLOG)

	def sig_handler(sig, frame):
		lg.info('exiting...')
		tracker.exit()
		sys.exit(0)

	signal.signal(signal.SIGINT, sig_handler)

	tracker.serve()
