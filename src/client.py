
import socket
import sys
import signal
from config import *
import logger as lg

def sig_handler(sig, frame):
	lg.info('exiting...')
	sys.exit(0)

signal.signal(signal.SIGINT, sig_handler)

class Client:
	def __init__(self, ip, port, username):
		self.ip = ip
		self.port = port
		self.username = username
		
	def askTracker(self, msg):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			try:
				sock.connect((TRACKER_IP, TRACKER_PORT))
			except ConnectionRefusedError:
				lg.error('connection with tracker refused')
				sys.exit()

			sock.send(msg.encode())

			reply_raw = sock.recv(4096)
			reply = reply_raw.decode()

			lg.debug('tracker reply:\n%s' % (reply))

			sock.close()

	def requestGroups(self):
		self.askTracker('gimme groups')



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
		inp = input('[%s]> ' % (username))
		
		if inp.startswith('!lg'):
			client.requestGroups()
		
		elif inp.startswith('!lm'):
			print('ok')

		elif inp.startswith('!j'):
			print('ok')

		elif inp.startswith('!w'):
			print('ok')

		elif inp.startswith('!e'):
			print('ok')

		elif inp.startswith('!q'):
			print('ok')

		#elif inp.startswith('!h'):
		#	help?

		else:
			lg.error('invalid ui command')
