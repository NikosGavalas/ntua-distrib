
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

	def getIp(self):
		return self.ip

	def getPort(self):
		return self.port

	def getUsername(self):
		return self.username

	def toDict(self):
		return {'Ip': self.ip, 'Port': self.port, 'Username': self.username, 'Uid': self.getUid()}


class Group:
	def __init__(self, name):
		self.name = name
		self.members = []

	def addMember(self, member):
		self.members.append(member)

	def removeMember(self, member):
		self.members.remove(member)

	def getMembers(self):
		return self.members

	def clearMembers(self):
		self.members.clear()

	def getName(self):
		return self.name

	def __str__(self):
		return self.name

