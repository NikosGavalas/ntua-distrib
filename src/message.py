
import json


RequestType = {}
RequestType['ListGroups'] = 1
RequestType['JoinGroup'] = 2
RequestType['Register'] = 3
RequestType['ListMembers'] = 4
RequestType['ExitGroup'] = 5
RequestType['Quit'] = 6

def forgeRequest(typ, content):
	return json.dumps({'Type': typ, 'Content': content}, indent=4)

def parseRequest(request):
	ret = json.loads(request)
	return ret['Type'], ret['Content']

def forgeReply(success, content):
	return json.dumps({'Success': success, 'Content': content}, indent=4)

def parseReply(reply):
	ret = json.loads(reply)
	return ret['Success'], ret['Content']

def forgeMessage(group, username, content, srcip, srcport):
	return json.dumps({'Group': group, 'Username': username, 'Content': content, 'SrcIp': srcip, 'SrcPort': srcport})

def parseMessage(message):
	ret = json.loads(message)
	return ret['Group'], ret['Username'], ret['Content'], ret['SrcIp'], ret['SrcPort']
