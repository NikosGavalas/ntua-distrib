
import subprocess as sub

ADDRESSES = ['distrib-1', 'distrib-2', 'distrib-3', 'distrib-4', 'distrib-5']
BASE_PORT = 46663

ROOT_PATH = '/home/distrib34/distrib/src/'
NUM_OF_CLIENTS = 5
TOTAL_ORDERING = False


def openRemoteProcess(name, node, executable):
	sub.run(['screen', '-S', name, '-dm', 'ssh',
          '-t', node, 'python3', executable])


def closeRemoteProcess(name):
	sub.run(['screen', '-S', name, '-X', 'quit'])


# Tracker
#args = ip, port, use_seq, seq_ip, seq_port
openRemoteProcess('tracker', 'distrib-4', ROOT_PATH + 'tracker.py ' + args)


# Sequencer
if TOTAL_ORDERING:
	#args = ip, port, name
	openRemoteProcess('sequencer', 'distrib-5', ROOT_PATH + 'sequencer.py ' + args)


# Clients
for i in range(NUM_OF_CLIENTS):
	name = 'client' + str(i)
	addr = ADDRESSES[i % NUM_OF_CLIENTS]
	port = BASE_PORT + 2 + i
	filename = '../msg/messages.txt' + str(i + 1)

	# args = ip, port, name, file, use_seq, seq_ip, seq_port
	args = '%s %s %s %s' % (name, addr, port, filename, +use_seq?)

	openRemoteProcess(name, addr, 'emulator.py ' + args)
