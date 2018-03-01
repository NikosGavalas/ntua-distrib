
from time import strftime
from config import DEBUG


def formatLog(level, message):
	return '[%s] (%s) %s' % (level, strftime("%H:%M:%S"), message)

def debug(message):
	if DEBUG:
		print(formatLog('DEBUG', message))

def distinct(message):
	if DEBUG:
		print('\n>>>>>>>>>\n%s\n>>>>>>>>>\n' % str(message))

def error(message):
	print(formatLog('ERROR', message))

def info(message):
	print(formatLog('INFO', message))

def warn(message):
	print(formatLog('WARN', message))

def fatal(message):
	print(formatLog('FATAL', message))
