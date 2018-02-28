
import socket
import threading
import signal
import sys
from config import *
import logger as lg

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
		
		self.groups = []

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

			reply = 'OK...' + message

			lg.debug('replying to %s:%s with: %s' % (addr[0], str(addr[1]), reply))

			reply_raw = reply.encode()
			conn.sendall(reply_raw)
			
		conn.close()



if __name__ == '__main__':
	tracker = Tracker(TRACKER_IP, TRACKER_PORT, TRACKER_BACKLOG)

	tracker.serve()


