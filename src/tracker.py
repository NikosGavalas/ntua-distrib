
import socket
from threading import Thread
import signal
import sys
import argparse
import time

from logger import Logger
import message as msg
from peers import Member, Group, Groups, Members

lg = Logger()

class TCPServer:
	def __init__(self, address, backlog):
		self.address = address
		self.backlog = backlog

		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.socket.bind(self.address)
		except socket.error:
			lg.fatal('port binding failure')
			sys.exit(1)

		self.socket.listen(self.backlog)

	def getSocket(self):
		return self.socket

	def __enter__(self):
		return self.socket

	def __exit__(self, exc_type, exc_val, traceback):
		self.socket.close()


class Tracker:
	def __init__(self, address, backlog, using_seq):
		self.address = address
		self.backlog = backlog
		self.USE_SEQUENCER = using_seq
		
		self.groups = Groups()

		self.members = Members()

		server = TCPServer(self.address, self.backlog)
		self.sock = server.getSocket()

		lg.info('tracker listening on %s:%s' % self.address)

	def heartbeatDaemon(self):
		while True:
			time.sleep(60)
			
			for member in self.members.getMembers():
				member.decreaseTimeout(60)

				if member.getTimeout() < 0:
					self.groups.removeMemberFromAllGroups(member)
					self.members.deleteMember(member)

	def serve(self):
		t = Thread(target=self.heartbeatDaemon)
		t.daemon = True
		t.start()

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

		if reqType == msg.RequestType.Register:
			ip = reqContent['Ip']
			port = reqContent['Port']
			username = reqContent['Username']
			
			member = self.members.getMemberByUsername(username)
			
			if member is None:
				member = Member((ip, port), username)
				self.members.addNewMember(member)

			uid = member.getUid()

			return msg.Reply(True, uid)

		if reqType == msg.RequestType.ListGroups:
			return msg.Reply(True, self.groups.getGroupsSerializable())

		if reqType == msg.RequestType.ListMembers:
			groupname = reqContent['Group']

			group = self.groups.getGroupByName(groupname)

			if group is None:
				return msg.Reply(False, [])

			return msg.Reply(True, group.getMembersSerializable())


		if reqType == msg.RequestType.JoinGroup:
			username = reqContent['Username']
			groupname = reqContent['Group']

			member = self.members.getMemberByUsername(username)

			if member is None:
				return msg.Reply(False, [])
			
			group = self.groups.getGroupByName(groupname)

			if group is None:
				group = Group(groupname)
				self.groups.addNewGroup(group)
				
				if self.USE_SEQUENCER:
					seq = self.members.getMemberByUsername('sequencer')
					group.addMember(seq)

			group.addMember(member)

			return msg.Reply(True, group.getMembersSerializable())
		
		if reqType == msg.RequestType.ExitGroup:
			username = reqContent['Username']
			groupname = reqContent['Group']

			member = self.members.getMemberByUsername(username)

			group = self.groups.getGroupByName(groupname)

			if group is not None:
				group.removeMember(member)

			return msg.Reply(True, '')

		if reqType == msg.RequestType.Quit:
			username = reqContent['Username']

			member = self.members.getMemberByUsername(username)

			self.groups.removeMemberFromAllGroups(member)
				
			self.members.deleteMember(member)

			return msg.Reply(True, '')

		if reqType == msg.RequestType.Heartbeat:
			username = reqContent['Username']

			member = self.members.getMemberByUsername(username)
			
			member.increaseTimeout(60)

			return msg.Reply(True, '')

		return msg.Reply(False, '')


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('addr', help="the tracker's address in the \
	                     form of host:port (e.g. 123.123.123.123:12345)")
	parser.add_argument('-b', help="backlog of tracker's socket, default is 10", type=int, default=10)
	parser.add_argument('-v', help='verbose output (use for debugging)', action='store_true', default=False)
	parser.add_argument('--seq_addr', help="use for total ordering - the sequencer's address in the \
	                     form of host:port (e.g. 123.123.123.123:12345)")
	args = parser.parse_args()

	addr = args.addr.split(':')
	TRACKER_ADDR = (addr[0], int(addr[1]))
	TRACKER_BACKLOG = args.b

	if args.v:
		lg.setDEBUG()

	USE_SEQUENCER = args.seq_addr is not None
	if USE_SEQUENCER:
		addr = args.seq_addr.split(':')
		SEQUENCER_ADDR = (addr[0], int(addr[1]))
		lg.info('using sequencer on %s:%s' % SEQUENCER_ADDR)

	tracker = Tracker(TRACKER_ADDR, TRACKER_BACKLOG, USE_SEQUENCER)

	def sig_handler(sig, frame):
		lg.info('exiting...')
		tracker.exit()
		sys.exit(0)

	signal.signal(signal.SIGINT, sig_handler)

	if USE_SEQUENCER:
		tracker.members.addNewMember(Member(SEQUENCER_ADDR, 'sequencer'))

	tracker.serve()
