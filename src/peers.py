
from hashlib import sha256

class Member:
	def __init__(self, ip, port, username):
		self.ip = ip
		self.port = port
		self.username = username

	def getUid(self):  # <-- yeah this is bad, I know
		concat = str(self.ip) + str(self.port) + str(self.username)

		self.uid = sha256(concat.encode()).hexdigest()[:10]

		return self.uid

	def toDict(self):
		return {'Ip': self.ip, 'Port': self.port, 'Username': self.username, 'Uid': self.getUid()}


class Group:
	def __init__(self, name):
		self.name = name
		self.members = []

	def addMember(self, member):
		self.members.append(member)

	def getMembers(self):
		return self.members

	def __str__(self):
		return self.name

