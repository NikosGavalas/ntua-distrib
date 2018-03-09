
import json


class RequestType:
	ListGroups = 1
	JoinGroup = 2
	Register = 3
	ListMembers = 4
	ExitGroup = 5
	Quit = 6


class MessageType:
	Hello = 1
	Application = 2
	Bye = 3


class Request:
	def __init__(self, typ, content):
		self.typ = typ
		self.content = content

	def __str__(self):
		ret = {}

		ret['Type'] = self.typ
		ret['Content'] = self.content

		return json.dumps(ret, indent=4)

	@staticmethod
	def fromString(rawString):
		ret = json.loads(rawString)
		return Request(ret['Type'], ret['Content'])

	def getType(self):
		return self.typ

	def getContent(self):
		return self.content
	
	
class Reply():
	def __init__(self, success, content):
		self.success = success
		self.content = content

	def __str__(self):
		ret = {}

		ret['Success'] = self.success
		ret['Content'] = self.content

		return json.dumps(ret, indent=4)

	@staticmethod
	def fromString(rawString):
		ret = json.loads(rawString)
		return Reply(ret['Success'], ret['Content'])

	def getSuccess(self):
		return self.success

	def getContent(self):
		return self.content


class Message():
	def __init__(self, typ, group, username, content, srcIp, srcPort, counter, origin):
		self.typ = typ
		self.group = group
		self.username = username
		self.content = content
		self.srcIp = srcIp
		self.srcPort = srcPort
		self.counter = counter
		self.origin = origin
	
	def __str__(self):
		ret = {
			"Type": self.typ,
			"Group": self.group,
			"Username": self.username,
			"Content": self.content,
			"SrcIp": self.srcIp,
			"SrcPort": self.srcPort,
			"Counter": self.counter,
			"Origin": self.origin
		}

		return json.dumps(ret, indent=4)

	@staticmethod
	def fromString(rawString):
		ret = json.loads(rawString)
		return Message(ret["Type"], ret["Group"], ret["Username"],
		               ret["Content"], ret["SrcIp"], ret["SrcPort"], ret["Counter"],
		               ret["Origin"])

	def getType(self):
		return self.typ

	def getContent(self):
		return self.content

	def getGroupName(self):
		return self.group

	def getSrcAddress(self):
		return (self.srcIp, self.srcPort)

	def getUsername(self):
		return self.username

	def getCounter(self):
		return self.counter
	
	def getOrigin(self):
		return self.origin
