#!/usr/bin/python

"""
URL Puller - pulls the source and parses links from a specified website.
It also writes those links to a .txt file called links_from_linkpuller.txt
"""

import urllib2
import sys

usage = '''
link_puller.py coded by: bostonlink @ pentest-labs.org
example: ./link_puller.py http://pentest-labs.org
'''

def main():
	if len(sys.argv) != 2:
		print(usage)
		return

	url_html = urllib2.urlopen(sys.argv[1])
	html_read = url_html.read()
	
	f = open('links_from_linkpuller.txt', 'a')
	
	for url in html_read.split():
		if 'http://' in url:
			if 'href=' in url:
				urls = url.lstrip('href=').split('>')
				for i in urls:
					if 'http://' in i:
						output = i.lstrip("'\"").rstrip("'\"")
						print (output)
						f.write(output + '\n')
		else:
			continue
			
	f.close()
			
if __name__ == '__main__':
	main()
