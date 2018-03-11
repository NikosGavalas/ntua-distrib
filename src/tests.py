
""" Helper script to execute tests.

Uses 'screen' to spawn remote processes (clients-trackers) via ssh.
If you want to see the the stdout of some process use 'screen -ls' to see the 
available sockets and 'screen -r <socketname>' to attach to a socket. Then 
use Ctrl+A and D to detach. """

import subprocess as sub
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('n', help='number of clients', type=int, action='store')
parser.add_argument('p', help='base port', type=int, action='store')
parser.add_argument('-t', help='use total ordering (sequencer)', action='store_true', default=False)
parser.add_argument('-c', help='close all remote processes', action='store_true', default=False)
cmd_args = parser.parse_args()

HOSTS = ['distrib-1', 'distrib-2', 'distrib-3', 'distrib-4', 'distrib-5']
BASE_PORT = cmd_args.p or 46663

ROOT_PATH = '/home/distrib34/distrib/src/'
TOTAL_ORDERING = cmd_args.t
NUM_OF_CLIENTS = cmd_args.n

CLOSE_ALL = cmd_args.c


def openRemoteProcess(name, node, executable):
	cmd = ['screen', '-S', name, '-dm', 'ssh',
            '-t', node, 'python3', executable]
	print('running: ' + ' '.join(cmd))
	sub.run(cmd)


def closeRemoteProcess(name):
	cmd = ['screen', '-S', name, '-X', 'quit']
	print('running: ' + ' '.join(cmd))
	sub.run(cmd)


tracker_host = HOSTS[3]
tracker_port = BASE_PORT
sequencer_host = HOSTS[4]
sequencer_port = BASE_PORT + 1

if CLOSE_ALL:
	closeRemoteProcess('tracker')
	if TOTAL_ORDERING:
		closeRemoteProcess('sequencer')
	for i in range(NUM_OF_CLIENTS):
		closeRemoteProcess('client' + str(i))
	sys.exit(0)

# Tracker
args = '--seq_addr %s:%s ' % (sequencer_host, sequencer_port) if TOTAL_ORDERING else ''
args += '%s:%s' % (tracker_host, tracker_port)
openRemoteProcess('tracker', tracker_host, ROOT_PATH + 'tracker.py ' + args)

# Sequencer
if TOTAL_ORDERING:
	args = '%s:%s' % (sequencer_host, sequencer_port)
	openRemoteProcess('sequencer', sequencer_host, ROOT_PATH + 'sequencer.py ' + args)

# Clients
clients_base_port = BASE_PORT + 2
for i in range(NUM_OF_CLIENTS):
	name = 'client' + str(i)
	host = HOSTS[i % len(HOSTS)]
	port = clients_base_port + i
	filename = '../msg/messages' + str(i + 1) + '.txt '

	args = '%s:%s ' % (host, port)
	args += '-s ' if TOTAL_ORDERING else ''
	args += '-t ' + filename
	args += name
	args += ' %s:%s' % (tracker_host, tracker_port)

	openRemoteProcess(name, host, ROOT_PATH + 'client.py ' + args)


