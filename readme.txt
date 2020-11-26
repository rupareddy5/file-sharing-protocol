pip install tqdm

for 1st client/server - $> cd s1 && python2 server1.py

for 2nd client/server - $> cd s2 && python2 server2.py


Commands :

1)
	$> IndexGet Shortlist <starttimestamp> <endtimestamp>

	#bonus

	$> IndexGet Shortlist <starttimestamp> <endtimestamp> pdf

	#bonus

	$> IndexGet Shortlist <starttimestamp> <endtimestamp> txt

	$> IndexGet Longlist

	#bonus

	$> IndexGet Longlist Programmer
	


2)
	$> FileHash Verify <filename>

	$> FileHash Checkall

3)
	$> FileDownload <filename>

4) 
	$> Cache Verify <filename>

	$> Cache Show

#################  NOTE ###############
1)Run Server1 and Run Server2
2)Both the codes should be run in python2
3)All ouptuts of sizes are in Bytes
4)Cache limit is 5mb
5)History is stored in history_1.log in server1 and history_2.log in server2