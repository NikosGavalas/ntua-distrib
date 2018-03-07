
from time import strftime
from config import DEBUG


def formatLog(level, message):
	return '[%s] (%s) %s' % (level, strftime("%H:%M:%S"), message)

def debug(message):
	if DEBUG:
		print(formatLog('DEBUG', message), flush=True)

def distinct(message):
	if DEBUG:
		print('\n>>>>>>>>>\n%s\n>>>>>>>>>\n' % str(message), flush=True)

def info(message):
	print(formatLog('INFO', message), flush=True)

def warn(message):
	print(formatLog('WARN', message), flush=True)

def error(message):
	print(formatLog('ERROR', message), flush=True)

def fatal(message):
	print(formatLog('FATAL', message), flush=True)
