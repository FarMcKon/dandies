#!/usr/bin/python

# Simple program which opens a file of urls, retrives their headers and prints them to tty and writes to a file

import urllib2
import sys

usage = '''
Port 80 Headers - Multiple site list
Author: bostonlink
Usage:  ./80headers.py url_list'
Notes: Use a custom list of urls, each url should be on a new line.
eg: 
http://google.com
http:yahoo.com
if there is an empty new line at the end of the file, the script will terminate when the '\n' newline is passed to it.
'''

if (len(sys.argv)!=2):
    print(usage)
    sys.exit(0)

usrfile = open(sys.argv[1], 'r')
outfile = open('output.txt', 'w')
outfile.close()
    
urls = usrfile.readlines()

for url in urls:
    if url == '\n':
        break
    else:
        url.rstrip()
        header = urllib2.urlopen(url).info()
        print('=' * 60)
        print(url)
        print('-' * 60)
        print(header)
        print('=' * 60)
        print('')
        f = open('output.txt', 'a')
        f.write(('=' * 60) + '\n' )
        f.write(url)
        f.write(('-' * 60) + '\n')
        f.write(str(header))
        f.close()

usrfile.close()



