
from time import strftime


class Logger():

	# TODO: could also use a fd to log to a file
	def __init__(self):
		self.DEBUG = False
		self.FLUSH = True
		self.PROFILING = False
		self.profile_info = '|  |  |  |\n| -- | -- | -- |\n'

	def setDEBUG(self):
		self.DEBUG = True

	def setPROFILE(self):
		self.PROFILING = True

	def _formatLog(self, level, message):
		return '[%s] (%s) %s' % (level, strftime("%H:%M:%S"), message)

	def debug(self, message):
		if self.DEBUG:
			print(self._formatLog('DEBUG', message), flush=self.FLUSH)

	def distinct(self, message):
		if self.DEBUG:
			print('\n>>>>>>>>>\n%s\n>>>>>>>>>\n' % str(message), flush=self.FLUSH)

	def info(self, message):
		print(self._formatLog('INFO', message), flush=self.FLUSH)

	def warn(self, message):
		print(self._formatLog('WARN', message), flush=self.FLUSH)

	def error(self, message):
		print(self._formatLog('ERROR', message), flush=self.FLUSH)

	def fatal(self, message):
		print(self._formatLog('FATAL', message), flush=self.FLUSH)

	def profile(self, message):
		if self.PROFILING:
			self.profile_info += message

	def report(self):
		if self.PROFILING:
			print('\n' + self.profile_info)