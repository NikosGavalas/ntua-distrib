
import json


RequestType = {}
RequestType['ListGroups'] = 1
RequestType['JoinGroup'] = 2
RequestType['Register'] = 3
RequestType['ListMembers'] = 4

def forgeRequest(typ, content):
	return json.dumps({'Type': typ, 'Content': content}, indent=4)

def parseRequest(request):
	deserialized = json.loads(request)

	return deserialized['Type'], deserialized['Content']

def forgeReply(success, content):
	return json.dumps({'Success': success, 'Content': content}, indent=4)

def parseReply(reply):
	deserialized = json.loads(reply)

	return deserialized['Success'], deserialized['Content']
