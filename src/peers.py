
from hashlib import sha256


class Member:
	def __init__(self, address, username):
		self.address = address
		self.username = username

		concat = self.address[0] + str(self.address) + self.username
		self.uid = sha256(concat.encode()).hexdigest()[:10] # <-- yeah this is bad, I know

	def getUid(self):
		return self.uid

	def getAddress(self):
		return self.address

	def getUsername(self):
		return self.username

	def toDict(self):
		return {'Ip': self.address[0], 'Port': self.address[1], 'Username': self.username, 'Uid': self.uid}


class Group:
	def __init__(self, name):
		self.name = name
		self.members = []

	def addMember(self, member):
		if member not in self.getMembers():
			self.members.append(member)

	def getMembersSerializable(self):
		return [member.toDict() for member in self.members]

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


class Groups:
	def __init__(self):
		self.groups = []

	def addNewGroup(self, group):
		self.groups.append(group)

	def removeGroupByName(self, groupname):
		group = self.getGroupByName(groupname)
		
		if group is not None:
			group.clearMembers()
			self.groups.remove(group)

	def getGroupByName(self, groupname):
		for group in self.groups:
			if group.getName() == groupname:
				return group
		return None

	def getGroupsSerializable(self):
		return [str(group) for group in self.groups]

	def removeMemberFromAllGroups(self, member):
		for group in self.groups:
			if member in group.getMembers():
				group.removeMember(member)


class Members:
	def __init__(self):
		self.members = []

	def addNewMember(self, newMem):
		self.members.append(newMem)

	def getMemberByUsername(self, username):
		for member in self.members:
			if member.getUsername() == username:
				return member
		return None

	def deleteMember(self, member):
		self.members.remove(member)