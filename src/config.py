# Set to true for diplaying debug messages
DEBUG = False

# Tracker address and socket backlog
TRACKER_ADDR = ('127.0.0.1', 46663)
TRACKER_BACKLOG = 10

# Use sequencer for FIFO *and* total ordering of the messages
USE_SEQUENCER = False
SEQUENCER_ADDR = ('127.0.0.1', 46664)

# Set to false only if executing tests
INTERACTIVE_CLI_MODE = True
