## AcChat version 0.2.1b ##

AcChat is a twisted powered chat server
> aimed to serve a PAD like Flex/Flash player with flying comments effects
> using a self-designed json-based protocol(see API)
> developed by observer(jingchaohu@gmail.com)

The name "AcChat" comes from "Anime Comic Chating Server"

Copyright (c) observer(jingchaohu@gmail.com)
This project is licensed under GPLv3, see LICENSE


## PREREQUIREMENTS ##
  * 1. python 2.6 and newer (2.5,2.4 might work but not tested)
  * 2. twisted 10.0 and newer (old versions might work but not tested)
  * 3. Mysql installed( or you can diy the db operations in db.py to fit your needs)
  * 4. python-mysqldb
  * 5. a setuped database (for convinience, I made a script doing this, see CONFIGRUATION section)


## INSTALL ##
  * unpack the files to any directeries and that's it


## CONFIGURATION ##
  * 1. edit db.py, set DBNAME, DBUSER, DBPWD
  * 2. edit acc.tac, set PORT, and if you want to, set BAN\_COUNT, MSGLOG\_TIMEOUT, BANLIST\_TIMEOUT, see comments in acc.tac for details
  * 3. create database if you don't have one
> > (shell)$ python db.py createdb


## DEBUG ##
  * 1. (in one shell)$ twistd -ny acc.tac
  * 2. (in another shell)$ telnet localhost PORT
  * 3. test apis according to the API document


## RUN/DEPLOYMENT ##
  * (shell)$ twistd -y acc.tac


## OTHERS ##
  * There are some sample codes in as3 directory for the Flex Player Class, this is not a part of AcChat Server, but it is necessary for flex player as a client. Those codes are also licensed under MIT LICENSE.


## TODO ##
  * 1. extend the api, eg. comment deleting, interactive banning/unbanning, etc
  * 2. design test scripts to do tests easily
  * 3. Do anything feasible and useful on request