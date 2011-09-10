#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# whatismyip.py
# 
# Version: 1.0
# 
# Copyright (C) 2010  novacane novacane[at]dandies[dot]org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import urllib2
from getpass import getpass

def main():
    
    url = "http://cfaj.freeshell.org/ipaddr.cgi"
    user_agent =  "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"
    headers = { "User-Agent" : user_agent }

    req = urllib2.Request(url, None, headers)
    
    try:
        response = urllib2.urlopen(req)
    except IOError, e: # HTTPError is a subclass of IOError.
        if e.code == 407:
            print "407 Proxy Authentication Required"
            proxy_user = raw_input("Proxy-Username: ")
            proxy_pswd = getpass("Proxy-Password: ")
            proxy_support_auth = urllib2.ProxyHandler({ \
                "http": "http://%s:%s@%s:%s" % (proxy_user, proxy_pswd, "172.16.1.96", "8080")})
            opener = urllib2.build_opener(proxy_support_auth)
            urllib2.install_opener(opener)
            response = urllib2.urlopen(req)
    
    print response.read().replace("\n", "")

if __name__ == '__main__':
    main()