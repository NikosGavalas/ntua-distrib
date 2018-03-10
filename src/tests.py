
import client as c
import tracker as t
import sequencer as s
from config import *

#ADDRESSES = ['distrib-1', 'distrib-2', 'distrib-3', 'distrib-4', 'distrib-5']
ADDRESSES = ['127.0.0.1']
BASE_PORT = 46663

# Tracker
tracker = t.Tracker(('distrib-4', BASE_PORT), TRACKER_BACKLOG)

# Clients
NUM_OF_CLIENTS = 5

clients = []

for i in range(NUM_OF_CLIENTS):
	newClient = Client((addresses[i]), base_port + i)
	clients.append(newClient)
