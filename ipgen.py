#!/usr/bin/env python
""" 
Random IP generater.

whoami project

http://darkc0de.com
d3hydr8[at]gmail[dot]com
"""

import sys
import random
import re

def randip():
	
	a = random.randrange(255) + 1
	b = random.randrange(255) + 1
	c = random.randrange(255) + 1
	d = random.randrange(255) + 1
	ip = "%d.%d.%d.%d" % (a,b,c,d)
	return ip


print "\n   d3hydr8[at]gmail[dot]com IPgen v1.0"
print "----------------------------------------\n"

if len(sys.argv) < 2:
	print "Usage: ./ipgen.py <how many?>\n"
	sys.exit(1)

def main():
	ips = []
	for x in xrange(int(sys.argv[1])):
		ips.append(randip())
		
	ips = str(ips)

	ips = ips[1:-1].replace("'","")
	print re.sub("\s","",ips)

if __name__=='__main__':
	main()
