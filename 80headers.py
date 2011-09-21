#!/usr/bin/python

# Simple program which opens a file of urls, retrieves their headers and prints them to tty and writes to a file

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

if (len(sys.argv)!=2):  # This checks to make sure you are using the script correctly. 
    print(usage)        # If you aren't, it prints the usage.
    sys.exit(0)

try: 
    usrfile = open(sys.argv[1], 'r') # except block here for file error.
except IOError:
    print usage, "\n That file didn't work. Try another file with a list of urls."
    sys.exit(0)
         
outfile = open('output.txt', 'w')
outfile.close()
urls = usrfile.readlines()
f = open('output.txt', 'a')

for url in urls:
    
    if url == '\n':     # As soon as the script runs into a new line in usrfile, it breaks.
        break
    else:
        try:
            header = urllib2.urlopen(url).info() # sets header variable to a string which is the meta info of url.
        except urllib2.URLError: 
            print "Sorry. We could not contact this url.", url
            continue
        url.rstrip()    # Return a copy of url with whitespace characters removed.
        header = urllib2.urlopen(url).info() 
        print('=' * 60) # Just some borders to the text.
        print(url)
        print('-' * 60)
        print(header)
        print('=' * 60)
        print('')
        f.write(('=' * 60) + '\n' )
        f.write(url)
        f.write(('-' * 60) + '\n')
        f.write(str(header))
        
f.close()
usrfile.close()

def main():
    pass
    
if __name__ == "__main__":
    main()


