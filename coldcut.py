#!/usr/local/bin/python -*- Mode: Python; tab-width: 4 -*-

'''coldcut v 0.2 - a bulk scanner for certain ESMTP Features

coldcut reads hostnames (or better IP addresses) from stdin.  It tries
to connect the hosts on port 25, issue an EHLO command and then a
QUIT. Im a certain ESMTP feature is present at the host it outputs its
IP.

By using the excellent medusa framework coldcut is able to scan
several hounderd hosts at once - if your OS can handle this.

For further enlightment on ESMTP see RFC 1869 (SMTP Service Extensions).

python -O coldcut.py < List

--drt@un.bewaff.net - http://c0re.23.nu/

'''

version = '$Id: coldcut.py,v 1.4 2001/12/05 22:49:30 drt Exp $'

# TODO:
# sort resp output
# generate statistics
# gnerate address lists

# issue this commands
surveycommands = ['EHLO survey.c0re.23.nu',
                  'QUIT']

# max time we wait for a sucessfull data gathering process
timeout = 66

# number of concurrent querys this might be limited by your OS
# Win 95: 55, Linux 2.0: 245, Linux 2.2: 1000
# FreeBSD, NT: 1000; can be tweaked for more.
concurrency = 222

import sys
import socket
import time
import select
import asyncore
import asynchat

def monitor():
    '''reap stale and open new connenctions until we reach concurrency'''

    # from work_in_progress/reaper.py
    # 'bring out your dead, <CLANG!>... bring out your dead!'
    now = int(time.time())
    for x in asyncore.socket_map.keys():
        s =  asyncore.socket_map[x]
        if hasattr(s, 'timestamp'):
            if (now - s.timestamp) > timeout:
                print >>sys.stdout, 'reaping connection to', s.host
                s.close()

    # create new connections
    while len(asyncore.socket_map) < concurrency:
        line = sys.stdin.readline()
        if line[-1:] == '\n':
            line = line [:-1]
        if line != '':
            s = smtpscan(line)
        else:
            break

def loop():
    '''loop over our sockets and monitor connections'''

    if hasattr (select, 'poll') and hasattr (asyncore, 'poll3'):
        poll_fun = asyncore.poll3
    else:
        poll_fun = asyncore.poll

    while asyncore.socket_map:
        monitor()
        poll_fun(30.0, asyncore.socket_map)
        
                    
class smtpscan (asynchat.async_chat):
    '''class implementing the actual scan'''
    
    def __init__ (self, address):
        '''constuctor - opens connection'''
        asynchat.async_chat.__init__ (self)
        self.create_socket (socket.AF_INET, socket.SOCK_STREAM)
        self.set_terminator ('\r\n')
        self.buffer = ''
        self.host = address
        self.timestamp = int(time.time())
        self.resp = {}
        self.awaiting = 'BANNER'
        self.commands = [x for x in surveycommands]
        self.done = 0
        
        try:
            self.connect((address, 25))
        except:
            self.handle_error()
            self.close()

    def handle_connect(self):
        '''we have successfull connected'''
        # ... and ignore this fact
        pass
               
    def handle_error(self):
        '''print out error information to stderr'''
        print >>sys.stderr, "ERROR:", self.host, sys.exc_info()[1]
    
    def collect_incoming_data (self, data):
        '''collect data which was recived on the socket'''
        self.buffer = self.buffer + data
      
    def found_terminator (self):
        '''we have read a whole line and decide what do do next'''
        data = self.buffer
        self.buffer = ''
        # update timestamp
        self.timestamp = int(time.time())
        # save response
        if __debug__:
            print "<<", self.host, data
        if not self.resp.has_key(self.awaiting):
            self.resp[self.awaiting] = data + '\n'
        else:
            self.resp[self.awaiting] += data + '\n'
        # check if the server awaits a new command
        if data[3] == ' ' and len(self.commands) > 0:
            cmd = self.commands.pop(0)
            self.awaiting = cmd.split(' ')[0]
            self.push('%s\r\n' % (cmd))
            if __debug__:
                print ">>", self.host, cmd            

    def handle_close (self):
        '''when the connection is closed use monitor() to start new connections'''        
        self.close()
        if len(self.resp):
            print "(%r, %r)" % (self.host, self.resp)
        monitor()
               
# "main"
# use monitor() to fire up the number of connections we want
monitor()
# handle all the connection stuff
loop()


