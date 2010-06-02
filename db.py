#!/usr/bin/env python
#coding:utf-8
'''
This is a twisted powered chat server 
    developed by observer(jingchaohu@gmail.com)
	using a self-designed json-based protocol
	aimed to serve a PAD like Flex/Flash player with flying comments effect
This project is licensed under GPLv3, see LICENSE

---- DATABASE FUNCTIONS ----
'''
# Notes to DB Structure
# 1. the database is too big(20 Million records), partition is used for concurrency consideration
# 2. innodb is prefered, it consumes more memory but it worths
# 3. I convert date and ip to integer to reduce the space and increase efficiency, but that is not a good design
#
# DB STRUCTURE
# ============
#+----------+------------------+------+-----+---------+-------+
#| Field    | Type             | Null | Key | Default | Extra |
#+----------+------------------+------+-----+---------+-------+
#| partid   | double           | YES  | MUL | NULL    |       |
#| time     | float            | YES  |     | NULL    |       |
#| txt      | text             | YES  |     | NULL    |       |
#| date     | int(11)          | YES  | MUL | NULL    |       |
#| mode     | smallint(6)      | YES  |     | NULL    |       |
#| color    | int(11)          | YES  |     | NULL    |       |
#| fontsize | int(11)          | YES  |     | NULL    |       |
#| uid      | int(11)          | YES  | MUL | NULL    |       |
#| ipv4     | int(10) unsigned | YES  | MUL | NULL    |       |
#+----------+------------------+------+-----+---------+-------+
#
# INDEXES
# =======
# idx1: partid
# idx2: date
# idx3: uid
# idx4: ipv4


from twisted.enterprise import adbapi 
import MySQLdb

DBNAME = "acchat_demo"
DBUSER = "acchat_demo"
DBPWD = "acchat_demo"

dbpool = adbapi.ConnectionPool("MySQLdb", db=DBNAME,user=DBUSER,passwd=DBPWD)

# db operations for leaving a message here
def leavemsg(txn,partid,time,txt,date,mode,color,fontsize,uid,ipv4):
	txn.execute( '''insert into ac_subs_10p
				(partid,time,txt,date,mode,color,fontsize,uid,ipv4)
				values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
				''', ( float(partid), float(time),txt.encode('utf-8'),
				int(date), int(mode), int(color),
				int(fontsize), uid, ipv4 ) )
	txn.execute( '''update ac_stats set subs = subs + 1 where id = %s''',(int(float(partid)),) )
			
# db operations to get userid by apikey so that we know who is using the api
def getuid(txn,apikey):
	txn.execute('select uid from ac_apikeys where apikey=%s',apikey)
	x = txn.fetchone()
	if x:
		return x[0]
	else:
		return 0

# db operations to insert multiple records in one time
def batchmsg(txn,bmsg):
	txn.executemany('''insert into ac_subs_10p 
						(partid,time,txt,date,mode,color,fontsize,uid,ipv4)
						values (%s,%s,%s,%s,%s,%s,%s,%s,%s) ''', bmsg )

def createdb():
	db = MySQLdb.connect(db=DBNAME,user=DBUSER,passwd=DBPWD)
	c = db.cursor()
	c.execute('''
	CREATE TABLE `ac_subs_10p` (
	  `partid` double DEFAULT NULL,
	  `time` float DEFAULT NULL,
	  `txt` text,
	  `date` int(11) DEFAULT NULL,
	  `mode` smallint(6) DEFAULT NULL,
	  `color` int(11) DEFAULT NULL,
	  `fontsize` int(11) DEFAULT NULL,
	  `uid` int(11) DEFAULT NULL,
	  `ipv4` int(10) unsigned DEFAULT NULL,
	  KEY `subidxp1` (`partid`),
	  KEY `subidxp2` (`date`),
	  KEY `subidxp3` (`uid`),
	  KEY `subidxp4` (`ipv4`)
	) ENGINE=MyISAM DEFAULT CHARSET=latin1 
	PARTITION BY KEY (partid) PARTITIONS 10;
	''')

if __name__ == '__main__':
	import os,sys
	if len(sys.argv) == 2 and sys.argv[1] == 'createdb':
		createdb()
