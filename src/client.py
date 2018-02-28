
from config import *
import socket
import logger as lg
import sys

class Client:
	
	def __init__(self, ip, port, username):
		self.ip = ip
		self.port = port
		self.username = username


def parseArgs(args):
	if len(args) < 4:
		lg.fatal('incorrect arguments')
		sys.exit(1)

	return (args[1], args[2], args[3])


if __name__ == '__main__':

	print(sys.argv)

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
			print('ok')
		
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
