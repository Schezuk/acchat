#!/usr/bin/env python
#coding:utf-8
'''
This is a twisted powered chat server 
    developed by observer(jingchaohu@gmail.com)
	using a self-designed json-based protocol
	aimed to serve a PAD like Flex/Flash player with flying comments effect
This project is licensed under GPLv3, see LICENSE

---- TWISTED SERVER  ----
'''

from twisted.internet import epollreactor
epollreactor.install()

from twisted.internet import protocol,reactor
from twisted.protocols.basic import LineReceiver

from twisted.application.service import Application
from twisted.application import internet,app
from twisted.enterprise import adbapi 
from twisted.python import logfile
app.logfile.LogFile = logfile.DailyLogFile

from collections import deque,defaultdict
import json
import time

import common
import db

PORT = 1819 # server's listening port
BAN_COUNT = 50 # how many comments made by clients within MSGLOG_TIMEOUT will be considere a spam?
MSGLOG_TIMEOUT = 60*5 # message logs time outs, in seconds
BANLIST_TIMEOUT = 3600*24 # ban time in seconds

# do not change below unless you know what are you doing
RESULT_OK = "ok"
RESULT_ERROR = "error"
PROTOCOL_ONLINE = "online"
PROTOCOL_BANLIST = "banlist"
PROTOCOL_APIKEY = "apikey"
PROTOCOL_PARTID = "partid"
PROTOCOL_LEAVEMSG = "leavemsg"
PROTOCOL_BATCHMSG = "batchmsg"
PROTOCOL_DELMSG = "delmsg"

dbpool = db.dbpool

class AcChat(protocol.Protocol):
	'''
	This method is a variation of the original LineOnlyReceiver from twisted
	It accepts both '\n' and '\x00' as delimiters of the request, and a max length
	of MAX_LENGTH bytes.
	The lineReceiver method then handles the request according to the API(see API for details)	
	A parsed request then make further call(s) in Factory Class to do some loging, the return
	value is then again processed by the Protocol Class, AcChat, and respond to the client
	'''
	_buffer = ''
	delimiters = ['\n','\x00']
	MAX_LENGTH = 65536
	
	def __init__(self):
		self.uid = 0
		self.partid = 0.0
	
	def dataReceived(self, data):
		"""Translates bytes into lines, and calls lineReceived."""
		self._buffer += data
		#we already know that delimiters can only be the last character
		if self._buffer[-1] in self.delimiters:
			if self.transport.disconnecting:
				# this is necessary because the transport may be told to lose
				# the connection by a line within a larger packet, and it is
				# important to disregard all the lines in that packet following
				# the one that told it to close.
				return
			else:
				self.lineReceived(self._buffer)
				# clear buffer
				self._buffer = ''
		if len(self._buffer) > self.MAX_LENGTH:
			return self.lineLengthExceeded(self._buffer)

	def connectionMade(self):
		print "Got new client:"+self.transport.getPeer().host
		# set tcpkeepalive=1 in order to drop clients if they are no longer in the channel
		self.transport.setTcpKeepAlive(1)
		self.factory.clients.append(self)

	def connectionLost(self, reason):
		print "Lost a client!"
		self.factory.clients.remove(self)

	def lineReceived(self, data):
		print "received", repr(data)
		# return policy file for flex sandbox verification
		if data.startswith('<policy-file-request/>'):
			msg = "<?xml version=\"1.0\"?><cross-domain-policy><allow-access-from domain=\"*\" to-ports=\"%d\" /></cross-domain-policy>\x00" % PORT
			print msg
			self.transport.write(msg)
			return
		try:
			j = json.loads(data)
			if j['protocol'] == PROTOCOL_ONLINE:
				# return partids that in clients
				# with this we can do some online rankings as demostrated on avfun001.org
				online = []
				for x in self.factory.clients:
					if x.partid:
						online.append(x.partid)
				d = {"online":online}
				self.message(json.dumps(d))
				return 
			elif j['protocol'] == PROTOCOL_APIKEY:
				# log user identity according to the apikey
				# the dbpool is a adbapi call, it runs a blockable method and add callback to it
				#   actually it just forks a thread to run self.factory.apikey with argument j
				#   then the returned value of that thread will automatically callback 
				#   self.apikeyresult method, see twisted adbapi documents for details.
				# this mechanism is fequently applied to ensure the reliabliliy of the asynchronoused
				#   twisted server, otherwise the server may not reachable when it is blocked by db
				#   operations, though the db operations are very simple/quick and this situation
				#   is very unlikely to happen.
				dbpool.runInteraction(self.factory.apikey,j['apikey']).addCallback(self.apikeyresult)
				return
			elif j['protocol'] == PROTOCOL_PARTID:
				# set the channel(partid) for the client
				self.partid = j['partid']
				self.message('{"ok":"you are now in channel %s"}'%str(self.partid))
				return
			elif j['protocol'] == PROTOCOL_BANLIST:
				# return banlist: ('ip','bantime') pairs
				if self.factory.banlist == {}:
					self.message('{"ok":"Banlist is empty"}')
				else:
					self.message(json.dumps(self.factory.banlist))
				return 
			elif j['protocol'] == PROTOCOL_LEAVEMSG:
				# leave a comment for the video
				#   ip is logged and converted to integer to enhence the performance of further dict operations
				#   it calls the leavemsg method in factory which
				#      1. do some logging and spam filtering 
				#      2. log the msg to the database, by calling certain methods in db.py
				#   if the message is not a spam, the callback function (informclients), do exactly what it 
				#      claims: send the message to anyone who is in the same channel(partid), the flex client
				#      then display the message on the player. Further operations are beyond the scope of this
				#      program
				uid = self.uid
				ipv4 = common.str2ip(self.transport.getPeer().host)
				dbpool.runInteraction(self.factory.leavemsg,j,uid,ipv4,data).addCallback(self.informclients)
				return
			elif j['protocol'] == PROTOCOL_BATCHMSG:
				# protocols for multiple messages, the api is required for authentication
				if not self.uid:
					self.message('{"error":"please login first"}')
				else:
					uid = self.uid
					ipv4 = common.str2ip(self.transport.getPeer().host)
					dbpool.runInteraction(self.factory.batchmsg,j,uid,ipv4).addCallback(self.batchmsgresult)
				return
			self.message('{"error":"unknown protocol"}')
		except Exception as what:
			self.message('{"error":"%s"}'%what.__str__())

	def message(self, message):
		self.transport.write(message + '\n')
	

	def informclients(self,arg):
		# the callback function for message leaving
		succeeded,partid,data = arg
		if succeeded: # if not banned and is a valid msg
			# inform all clients that are listening on a specified partid the original data
			for x in self.factory.clients:
				if x.partid == partid:
					x.message(data)	
		else:
			self.message('{"error":"you\'re banned for %d seconds"}'%BANLIST_TIMEOUT)
	
	def apikeyresult(self,uid):
		# the callback function for api verification
		self.uid = uid
		if self.uid:
			self.message('{"ok":"your uid is %d"}'%self.uid)
		else:
			self.message('{"error":"you are not verified"}')

	def batchmsgresult(self,r):
		# the callback function for batch message leaving
		if r:
			self.message('{"ok":"batch message succeed!"}')
		else:
			self.message('{"error":"unknown failure!"}')

class AcFactory(protocol.Factory):
	'''
		Factories are global envirenments for each clinets
		It provides functions to 
			1. loging and filtering spams
			2. handle message leaving protocals
			3. handle apikey verification protocals
	'''
	protocol = AcChat
	def __init__(self):
		self.clients = []
		self.msglog = deque() # which maintains MSGLOG_TIMEOUT seconds recent client msgs(ip,timestamp)
		self.counter = defaultdict(int) # a counter to ips (for ban purpose)
		self.banlist = dict()

	def batchmsg(self,txn,j,uid,ipv4):
		# handling batchmsg protocol,return true if succeed and false if failed
		n = j['length']
		bmsg = []
		for x in j['data']:
			bmsg.append( [float(x['partid']),float(x['time']),x['txt'].encode('utf-8'),
					common.timestr2int(x['date']),int(x['mode']),int(x['color']),
					int(x['fontsize']),uid,ipv4] )
		try:
			db.batchmsg(txn,bmsg)
		except Exception as what:
			print what
			return False
		return True

	def apikey(self,txn,apikey):
		# return user identity(uid) of the according apikey
		# return 0 if the apikey is invalid
		try:
			return db.getuid(txn,apikey)
		except Exception as what:
			print what
		return 0

	def logip(self,ipv4):
		# logging
		self.msglog.append( [time.time(),ipv4] )
		self.counter[ipv4] += 1
		# check if too many posts
		if self.counter[ipv4] > BAN_COUNT:
			self.banlist[ipv4] = time.time()+BANLIST_TIMEOUT
			return False
		# check if already banned
		if self.banlist.has_key(ipv4):
			if self.banlist[ipv4] < time.time(): # unban if timeouted
				self.banlist.pop(ipv4)
			else:
				return False
		# clean timeouted log
		# the try block is used in case of empty msglogs.
		try:
			x = self.msglog.popleft()
			while time.time() - x[0] > MSGLOG_TIMEOUT:
				self.counter[ipv4] -= 1
				x = self.msglog.popleft()
			self.msglog.appendleft(x)
		except:
			pass
		return True

	def leavemsg(self,txn,j,uid,ipv4,data):
		# handling leavemsg protocol,return true if succeed and false if failed
		# the logip metho is called to do some in memory logging and spam filtering
		partid = j['partid']
		time = j['time']
		txt = j['txt']
		date = common.timestr2int(j['date'])
		mode = j['mode']
		color = j['color']
		fontsize = j['fontsize']
		# log and check if banned
		if not self.logip(ipv4):
			return False,partid,data
		# inerst into database
		try:
			db.leavemsg(txn,partid,time,txt,date,mode,color,fontsize,uid,ipv4)
		except Exception as what:
			print what
		return True,partid,data

# uncomment this and comment the last few lines to enable a standalone server
#if __name__ == '__main__':
#	reactor.listenTCP(1819,AcFactory())
#	reactor.run()

# twisted powered daemon server
# run:    twistd -ny acchat.tac
# debug:  twistd -y acchat.tac
application = Application("AcChat")
accService = internet.TCPServer(PORT,AcFactory())
accService.setServiceParent(application)
