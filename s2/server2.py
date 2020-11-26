import socket
import os
import re
import time
import hashlib
import stat
import signal
import sys
import subprocess 
from tqdm import tqdm



# creating socket objects for server1 and server2

server2 = socket.socket()
#print ("socket successfully created for 2") 
server1 = socket.socket()
#print ("socket successfully created for 1") 



#binding host for server2

server2.bind((socket.gethostname(),50000))
server2.listen(5)


server1.connect((socket.gethostname(),60000))



r1_conn, addr_1 = server2.accept()
#print ("got connection from address ",addr_1) 
print ("connected successfully") 

class TimedOutExc(Exception):
	pass

def handler(signum, frame):
	raise TimedOutExc()

signal.signal(signal.SIGALRM, handler)

directory_2 = os.path.dirname(os.path.realpath(__file__))
#we have to directory 1 as input 

#making command line and recieving input from user

def hash_value(name_file):
    md5hash = hashlib.md5()

    with open(name_file,"rb") as f:
	    for chunk in iter(lambda: f.read(4096), b""):
		    md5hash.update(chunk)

    return md5hash.hexdigest()


def all_hash(name_file):
    #pass
    for [dir_path,dir_name,filenames] in os.walk(directory_2+name_file):
        break
  #  print ("HI")
 #   print (dir_path,filenames,dir_name)
    for f in filenames:
        if f == "server2.py" or f == "history_2.log":
            continue
        status = os.stat(directory_2+name_file+"/"+f)
        hashingvalue = hash_value(directory_2+name_file+"/"+f)
        returning_value = name_file + "/" +f + '&' + hashingvalue + '&' + str(status.st_mtime)
        r1_conn.send(returning_value)
      #  print returning_value
        time.sleep(0.01)
    for d in dir_name:
        all_hash(name_file+"/"+d)
    return


def fetch_from_server(name_file):
    received = server1.recv(1024)
    if received == "WRONG":
        print  "Improper File Name" 
        return
    receiveds = received.split('&')
    filesize = int(receiveds[0])
    length=0
    total_size=0
    print 'Saving a copy of {} in the cache'.format(name_file) 
    dir_name = directory_2+'/'+"Cache"
    for dirpath,dirnames,filenames in os.walk(dir_name):
        for f in filenames:
            fp = os.path.join(dirpath,f)
            sizes=os.path.getsize(fp)
            total_size+=sizes

    if (total_size+filesize)>5000000 :
        for [dirpath,dirnames,filenames] in os.walk(dir_name):
            break
        files = [(os.path.join(dirpath,f)) for f in filenames]
        
        files.sort(key=os.path.getmtime, reverse=True) 
        i=0
        while (total_size) >= 5000000 and i<len(files):
            last_modified_file = None if len(files) == 0 else files[i]

            if last_modified_file is not None:
                os.remove(last_modified_file)
            total_size=0
            for dirpath,dirnames,filenames in os.walk(dir_name):
                for f in filenames:
                    fp = os.path.join(dirpath,f)
                    sizes=os.path.getsize(fp)
                    total_size+=sizes
            i+=1

    # content
    progress = tqdm(range(filesize), str("Receiving "+name_file),unit="B",unit_divisor=1024, unit_scale=False)
    with open(os.path.join('Cache',name_file),"wb") as f:
        for _ in progress:
            bytes_read = server1.recv(2048)
            if not bytes_read:
                break
            f.write(bytes_read)
            length += len(bytes_read)
            progress.update(len(bytes_read))
            if length == filesize:
                break
        progress.close()
    return f

def all_size(name_file):
    dir_name = directory_2+'/'+"Cache"
    for dirpath,dirnames,filenames in os.walk(dir_name):
        for f in filenames:
            fp = os.path.join(dirpath,f)
            sizes=os.path.getsize(fp)
            print f,sizes



prompt_time = 1
flag = 0
while True:
    if flag==0:
        directory_1 = server1.recv(1024)
        r1_conn.send(directory_2)
        print "Connected to directory",directory_1," from directory",directory_2
        flag = 1
        continue
    recieved = server1.recv(1024)
    if recieved == "EMPTY":
        a = 0
    else:
        log = open(directory_2+"/history_2.log","a+")
        log.write(recieved+" "+str(time.ctime(time.time())+"\n"))
        log.close()
        
        
        recieveds = recieved.split(" ")
        
        if recieveds[0] == "FileHash":
            print "Recieved Command is",recieved
            print "<s2 >",
            if recieveds[1] == "Verify":
                
                if len(recieveds) == 2:
                    r1_conn.send("WRONG")
                    continue
                name_file = recieveds[2]

                if os.path.exists(directory_2+'/'+name_file):
                    status = os.stat(directory_2+'/'+name_file)
                    hashvalue = hash_value(directory_2+'/'+name_file)
                    r1_conn.send(hashvalue+'&'+str(status.st_mtime))
   #                 print ("reached")
                else:
                    r1_conn.send("WRONG")
            elif recieveds[1] == "Checkall":
                all_hash("")
    #            print ("asdsadsa")
                time.sleep(0.02)
                r1_conn.send("completed")


        elif recieveds[0] == "FileDownload":
            print "Recieved Command is",recieved
            if len(recieveds) == 1:
                r1_conn.send("WRONG")
                continue
            name_file = recieveds[1]

            if os.path.exists(directory_2+'/'+name_file):
                status = os.stat(directory_2+'/'+name_file)
                hashvalue = hash_value(directory_2+'/'+name_file)
                filesize = os.path.getsize(directory_2+'/'+name_file)
                r1_conn.send(str(filesize)+'&'+str(status.st_mtime)+'&'+hashvalue)
                progress = tqdm(range(filesize),str("Sending "+name_file), unit="B",unit_scale=False,unit_divisor=1024) 
               
                length=0
                with open(name_file,"rb") as f:
                    for _ in progress:
                        # print("k")
                        bytes_read = f.read(2048)
                        if not bytes_read:
                            break
                        r1_conn.sendall(bytes_read)
                        length+=len(bytes_read)
                        progress.update(len(bytes_read))
                        if length==filesize:
                            break
                    progress.close()
     #           print("reached")
                prompt_time=1

            else:
                r1_conn.send("WRONG") 

        elif recieveds[0] == "IndexGet":
            print "Recieved Command is",recieved
            print "<s2 >",

            if recieveds[1] == "Shortlist" or recieveds[1]== "Longlist":
            
                ls = subprocess.Popen(["ls"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output,errors = ls.communicate()
                output = output+"completed"
                lines = output.split("\n")
                for l in lines:
                    if l!= "completed" and l!="server2.py":
                        status = os.stat(directory_2+'/'+l)
                        name_file = l
                        l = l + '&' + str(status.st_size) + '&' + str(status.st_mode) + '&' + str(status.st_mtime)
                        if len(recieveds)==3 :
                            if recieveds[1] == "Longlist" and recieveds[2] == "Programmer" and name_file.endswith('.txt'):
                                check_flag = 0

                                with open(name_file) as f:
                                    if "Programmer" in f.read():
                                        check_flag = 1
                                if check_flag == 1:
                                    r1_conn.send(l)
                                    continue
                                else:
                                    continue
                            elif  recieveds[1] == "Longlist" and recieveds[2] != "Programmer"  :
                                r1_conn.send(l)
                                
                        else:
                            r1_conn.send(l)
                            time.sleep(0.01)

                    elif l == "completed":
                        time.sleep(0.1)
                        r1_conn.send("completed")

        
        elif recieveds[0] == "Cache":
          #  print "<s2 >",

            if recieveds[1] == "Verify":
                name_file = recieveds[2]
                if os.path.exists(directory_2+'/'+name_file):
                    status = os.stat(directory_2+'/'+name_file)
                    hashvalue = hash_value(directory_2+'/'+name_file)
                    filesize = os.path.getsize(directory_2+'/'+name_file)
                    r1_conn.send(str(filesize)+'&'+str(status.st_mtime)+'&'+hashvalue)
                    progress = tqdm(range(filesize),str("Sending "+name_file), unit="B",unit_scale=False,unit_divisor=1024) 
                
                    length=0
                    with open(name_file,"rb") as f:
                        for _ in progress:
                            bytes_read = f.read(2048)
                            if not bytes_read:
                                break
                            r1_conn.sendall(bytes_read)
                            length+=len(bytes_read)
                            progress.update(len(bytes_read))
                            if length==filesize:
                                break
                        progress.close()
      #              print("reached")
                    prompt_time=1

                else:
                    r1_conn.send("WRONG") 



    signal.alarm(1)
    try:
        if prompt_time == 1:
            input = raw_input("<s2 >")
        else:
            input = raw_input()
            prompt_time = 1
        signal.alarm(0)
    #    print "Hello"
        inputs = input.split(" ")
        print "Executing the input ",inputs
        #signal.alarm(0)
       
        log = open(directory_2+"/history_2.log","a+")
        log.write(input+" "+time.ctime(time.time())+"\n")
        log.close()

        if inputs[0] == "FileHash":
            r1_conn.send(input)
            if inputs[1] == "Verify":
                if len(inputs) == 2:
                    print ("invalid command")
                    continue
                name_file = inputs[2]
                val = server1.recv(1024)
                if val == "WRONG":
                    print ("Improper File Name")
                    continue

                vals = val.split('&')

                hash_vals = vals[0]
                mtime = float(vals[1])
                print "CheckSum: ",hash_vals," ,TimeStamp: ",time.ctime(mtime)
            elif inputs[1] == "Checkall":
                while True:
                    val = server1.recv(1024)
                    if val == "completed":
                        break
                    else:
                        vals = val.split('&')
                        file_name = vals[0]
                        hash_vals = vals[1]
                        mtime = float(vals[2])
                        print "Filename: ",file_name," ","CheckSum: ",hash_vals," ","TimeStamp: ",time.ctime(mtime)
            else:
                print "invalid input"

        elif inputs[0] == "FileDownload":
            r1_conn.send(input)
            if len(inputs) == 1:
                print "Invalid command"
                continue
            name_file = inputs[1]
            received = server1.recv(1024)
        #    print received
            if received == "WRONG":
                print ("Improper File Name")
                continue
            receiveds = received.split('&')
            filesize = int(receiveds[0])
            timestamp = float(receiveds[1])
            hashvalue = receiveds[2]
            length=0
            progress = tqdm(range(filesize), str("Receiving "+name_file),unit="B",unit_divisor=1024, unit_scale=False)
            with open(name_file,"wb") as f:
                for _ in progress:
                    bytes_read = server1.recv(2048)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
                    length += len(bytes_read)
                    progress.update(len(bytes_read))
                    if length == filesize:
                        break
                progress.close()
            
            print "File: ",name_file,"Size of file: ",filesize,"Timestamp: ",time.ctime(timestamp),"MD5: ",hashvalue 

        elif inputs[0] == "IndexGet":
            r1_conn.send(input)
            if inputs[1] == "Shortlist":

                while True:
                    
                    val = server1.recv(1024)

                    if val == "completed":
                        break
                    else:
                        vals = val.split('&')
                        name_file = vals[0]
                        size = int(vals[1])
                        type_file = int(vals[2])
                        mtime = float(vals[3])
                        if  stat.S_ISDIR(type_file) !=0:
                            req_type = "Directory"
                        elif stat.S_ISREG(type_file) !=0:
                            req_type = "Regular file"
                        else:
                            req_type = "Others"

                        if float(inputs[2])<=mtime and float(inputs[3])>=mtime and len(inputs)==4:
                            print "Name- ",name_file," size- ",size," type- ",req_type," timestamp- ",mtime
                        elif float(inputs[2])<=mtime and float(inputs[3])>=mtime and len(inputs)==5  and inputs[4]=="pdf" and name_file.endswith('.pdf') :
                          #  print "hiii"
                            print "Name- ",name_file," size- ",size," type- ",req_type," timestamp- ",mtime
                        elif float(inputs[2])<=mtime and float(inputs[3])>=mtime and len(inputs)==5  and inputs[4]=="txt" and name_file.endswith('.txt'):
                          #  print "hiii"
                            print "Name- ",name_file," size- ",size," type- ",req_type," timestamp- ",mtime


            elif inputs[1] == "Longlist":


                while True:
                    
                    val = server1.recv(1024)

                    if val == "completed":
                        break
                    else:
                        vals = val.split('&')
                        name_file = vals[0]
                        size = vals[1]
                        type_file = int(vals[2])
                        mtime = float(vals[3])
                        if  stat.S_ISDIR(type_file) !=0:
                            req_type = "Directory"
                        elif stat.S_ISREG(type_file) !=0:
                            req_type = "Regular file"
                        else:
                            req_type = "Others"

                        print "Name- ",name_file," size- ",size," type- ",req_type," timestamp- ",mtime

        elif inputs[0] == "Cache":

            if inputs[1] == "Verify":

                filename = inputs[2]
                

                if os.path.isfile(filename):
                    print "Succesfully fetched from cache"
                    r1_conn.send("ok")
                else:
                    print "File is not present in cache"
                    print "Fetching from server"
                    r1_conn.send(input)
                   
                    content2 = fetch_from_server(filename)
                    if content2:
                        print "Succesfully fetched from server"
                    else:
                        print "There's no such file"
            
            if inputs[1] == "Show":
                r1_conn.send(input)
                all_size("")
            
    except TimedOutExc:
        prompt_time = 0
        signal.alarm(0)
      #  print "lllllll"
        r1_conn.send("EMPTY")
       # print "hi"
