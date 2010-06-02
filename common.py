#!/usr/bin/env python
#coding:utf-8
'''
This is a twisted powered chat server 
    developed by observer(jingchaohu@gmail.com)
	using a self-designed json-based protocol
	aimed to serve a PAD like Flex/Flash player with flying comments effect
This project is licensed under GPLv3, see LICENSE

---- SOME COMMON FUNCTIONS ----
'''

import time,calendar

def timestr2int(timestr,format='%Y-%m-%d %H:%M:%S'):
	return int(calendar.timegm( time.strptime(timestr,format) ))

def int2timestr(d,format='%Y-%m-%d %H:%M:%S'):
	return time.strftime( format, time.gmtime(d) ) 

def str2ip(ip):
	if ',' in ip:
		ip = ip[:ip.find(',')]
	ip = ip.split('.')
	ipv4 = 0
	for x in ip[:4]:
		ipv4 = ipv4*256 + int(x)
	return ipv4

def ip2str(ip):
	return '%s.%s.%s.%s' % (ip>>24,(ip>>16)&0xff,(ip>>8)&0xff,ip&0xff)

