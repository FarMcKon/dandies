#!/usr/bin/python
# Simple program which opens a file of urls, retrieves their headers and prints them to tty and writes to a file

import urllib2
import sys

usage = """
Port 80 Headers - Fetches url header information from site specified in a file 
Usage:  ./80headers.py url_list'

Notes: url_list is a text file, which a single url on each line.
	empty lines are skipped 

"""
	
	
def main():
	""" main function. checks for command parameters and tries to run them."""	
	if (len(sys.argv)!=2):  # This checks to make sure you are using the script correctly. 
		print(usage)        # If you aren't, it prints the usage.
		return 
	
	try: 
		usrfile = open(sys.argv[1], 'r') # except block here for file error.
	except IOError:
		print usage, "\n That file didn't work. Try another file with a list of urls."
		return
	
	#-- clears/reset the file if it has any previous/
	outfile = open('output.txt', 'w')
	outfile.close()
	
	urls = usrfile.readlines()
	f = open('output.txt', 'a')

	fatBorder = '=' * 60 #a line of =
	thinBorder = '-' * 60 #a line of -
	for url in urls:
		
		if url == '\n' or ( len(url) > 1 && url[0] == '#') :
			continue 
		else:
			try:
				header = urllib2.urlopen(url).info() # sets header variable to a string which is the meta info of url.
			except urllib2.URLError: 
				print "Sorry. We could not contact this url.", url
				continue
			url.rstrip()    # Return a copy of url with whitespace characters removed.
			header = urllib2.urlopen(url).info() 
			print(fatBorder) 
			print(url)
			print(thinBorder)
			print(header)
			print(fatBorder)
			print('')
			f.write(fatBorder + '\n' )
			f.write(url)
			f.write(fatBorder + '\n')
			f.write(str(header))
			
	f.close()
	usrfile.close()
    
if __name__ == "__main__":
    main()


