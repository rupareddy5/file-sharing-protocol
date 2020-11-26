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

server1 = socket.socket()
#print ("socket successfully created for 1")
server2 = socket.socket()
#print ("socket successfully created for 2")



# binding port for server1
server1.bind((socket.gethostname(),60000))
server1.listen(5)



r2_conn, addr_2 = server1.accept()
#print ("got connection from address ",addr_2)



server2.connect((socket.gethostname(),50000))
print "connected successfully"

class TimedOutExc(Exception):
	pass

def handler(signum, frame):
	raise TimedOutExc()


signal.signal(signal.SIGALRM, handler)

#making command line and recieving input from user
#we have to take directory_2 as input from other server

directory_1 = os.path.dirname(os.path.realpath(__file__))


def hash_value(name_file):
    md5hash = hashlib.md5()

    with open(name_file,"rb") as f:
	    for chunk in iter(lambda: f.read(4096), b""):
		    md5hash.update(chunk)

    return md5hash.hexdigest()


def all_hash(name_file):
    for [dir_path,dir_name,filenames] in os.walk(directory_1+name_file):
	    break
 #   print dir_path,filenames,dir_name
    for f in filenames:
        if f=="server1.py" or f == "history_1.log":
            continue
        status = os.stat(directory_1+name_file+"/"+f)
        hashingvalue = hash_value(directory_1+name_file+"/"+f)
        returning_value = name_file + "/" +f + '&' + hashingvalue + '&' + str(status.st_mtime)
        r2_conn.send(returning_value)
    for d in dir_name:
        all_hash(name_file+"/"+d)
    return


def all_size(name_file):
    dir_name = directory_1+'/'+"Cache"
    for dirpath,dirnames,filenames in os.walk(dir_name):
        for f in filenames:
            fp = os.path.join(dirpath,f)
            sizes=os.path.getsize(fp)
            print f,sizes


def fetch_from_server(name_file):
    received = server2.recv(1024)
    if received == "WRONG":
        print  "Improper File Name" 
        return
    receiveds = received.split('&')
    filesize = int(receiveds[0])
    length=0
    total_size=0
    print 'Saving a copy of {} in the cache'.format(name_file) 
    dir_name = directory_1+'/'+"Cache"
    for dirpath,dirnames,filenames in os.walk(dir_name):
        for f in filenames:
            fp = os.path.join(dirpath,f)
            sizes=os.path.getsize(fp)
            total_size+=sizes

    if (total_size+filesize)>=5000000 :
        for [dirpath,dirnames,filenames] in os.walk(dir_name):
            break
        files = [(os.path.join(dirpath,f)) for f in filenames]
        
        files.sort(key=os.path.getmtime, reverse=True) 
        print(files)
        # print("hi")
        i=0
        while (total_size+filesize) >= 5000000 and i<len(files) :
            # print(i,len(files))
            last_modified_file = None if len(files) == 0 else files[i]
            if last_modified_file is not None:
                # print(last_modified_file)
                os.remove(last_modified_file)
            # print("k")
            total_size=0
            for dirpath,dirnames,filenames in os.walk(dir_name):
                for f in filenames:
                    fp = os.path.join(dirpath,f)
                    sizes=os.path.getsize(fp)
                    total_size+=sizes
                    # print(total_size)
            i+=1

    # content
    progress = tqdm(range(filesize), str("Receiving "+name_file),unit="B",unit_divisor=1024, unit_scale=False)
    with open(os.path.join('Cache',name_file),"wb") as f:
        for _ in progress:
            bytes_read = server2.recv(2048)
            if not bytes_read:
                break
            f.write(bytes_read)
            length += len(bytes_read)
            progress.update(len(bytes_read))
            if length == filesize:
                break
        progress.close()
    return f



prompt_time = 1
flag = 0
while True:
    if flag == 0:
        r2_conn.send(directory_1)
        directory_2 = server2.recv(1024)
        print "Connected to directory",directory_2," connected from directory",directory_1
        flag = 1
        continue
    signal.alarm(1)
    try:
        if prompt_time == 1:
            input = raw_input("<s1 >")
        else:
            prompt_time = 1
            input = raw_input()
        signal.alarm(0)
        inputs = input.split(" ")
        log = open(directory_1+"/history_1.log","a+")
        log.write(input+" "+str(time.ctime(time.time())+"\n"))
        log.close()
        print "Executing the input ",inputs
        

        if inputs[0] == "FileHash":
            r2_conn.send(input)
           
            if inputs[1] == "Verify":
                if len(inputs) == 2:
                    print ("invalid command")
                    continue
                name_file = inputs[2]
                val = server2.recv(1024)
                if val == "WRONG":
                    print ("Improper File Name")
                    continue

                vals = val.split('&')

                hash_vals = vals[0]
                mtime = float(vals[1])
                print "CheckSum: ",hash_vals," ,TimeStamp: ",time.ctime(mtime)
            elif inputs[1] == "Checkall":
                while True:
                    val = server2.recv(1024)
                    if val == "completed":
                        break
                    else:
                   #     print val
                        vals = val.split('&')
                        file_name = vals[0]
                        hash_vals = vals[1]
                        mtime = float(vals[2])
                        print "Filename: ",file_name," ","CheckSum: ",hash_vals," ","TimeStamp: ",time.ctime(mtime)
            else:
                print "invalid input"

        elif inputs[0] == "FileDownload":
            r2_conn.send(input)
            
            if len(inputs) == 1:
                print "Invalid command"
                continue
            name_file = inputs[1]
            received = server2.recv(1024)
          #  print received
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
                    bytes_read = server2.recv(2048)
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
            r2_conn.send(input)
            
            if inputs[1] == "Shortlist":

                while True:
                    
                    val = server2.recv(1024)

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
                    
                    val = server2.recv(1024)

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
                    r2_conn.send("ok")
                else:
                    print "File is not present in cache"
                    print "Fetching from server"
                    r2_conn.send(input)
                   
                    content2 = fetch_from_server(filename)
                    if content2:
                        print "Succesfully fetched from server"
                    else:
                        print "There's no such file"
            
            if inputs[1] == "Show":
                r2_conn.send(input)
                all_size("")
              #  print "Done"     
            prompt_time=1       

    except TimedOutExc:
        signal.alarm(0)
        prompt_time = 0
        r2_conn.send("EMPTY")
   #     print "Hi" 

    recieved = server2.recv(1024)
    if recieved == "EMPTY":
        a = 0
    else:
        log = open(directory_1+"/history_1.log","a+")
        log.write(recieved+" "+str(time.ctime(time.time())+"\n"))
        log.close()
        
      #  print recieved
        recieveds = recieved.split(" ")
        
        if recieveds[0] == "FileHash":
            print "Recieved Command is",recieved

            print "<s1 >",
            
            if recieveds[1] == "Verify":
                
                if len(recieveds) == 2:
                    r2_conn.send("WRONG")
                    continue
                name_file = recieveds[2]

                if os.path.exists(directory_1+'/'+name_file):
                    status = os.stat(directory_1+'/'+name_file)
                    hashvalue = hash_value(directory_1+'/'+name_file)
                    r2_conn.send(hashvalue+'&'+str(status.st_mtime))
 #                   print ("reached")
                else:
                    r2_conn.send("WRONG")
            elif recieveds[1] == "Checkall":
                all_hash("")
            #    print ("asdsadsa")
                time.sleep(0.02)
                r2_conn.send("completed")


        elif recieveds[0] == "FileDownload":
            print "Recieved Command is",recieved

            if len(recieveds) == 1:
                r2_conn.send("WRONG")
                continue
            name_file = recieveds[1]

            if os.path.exists(directory_1+'/'+name_file):
                status = os.stat(directory_1+'/'+name_file)
                hashvalue = hash_value(directory_1+'/'+name_file)
                filesize = os.path.getsize(directory_1+'/'+name_file)
                r2_conn.send(str(filesize)+'&'+str(status.st_mtime)+'&'+hashvalue)
                progress = tqdm(range(filesize),str("Sending "+name_file), unit="B",unit_scale=False,unit_divisor=1024) 
               

                with open(name_file,"rb") as f:
                    for _ in progress:
                        # print("k")
                        bytes_read = f.read(2048)
                        if not bytes_read:
                            break
                        r2_conn.sendall(bytes_read)
                        progress.update(len(bytes_read))
                    progress.close()
  #              print("reached")
                prompt_time=1


            else:
                r2_conn.send("WRONG") 

        elif recieveds[0] == "IndexGet":
            print "Recieved Command is",recieved

            print "<s1 >",

            if recieveds[1] == "Shortlist" or recieveds[1]== "Longlist":
            
                ls = subprocess.Popen(["ls"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output,errors = ls.communicate()
                output = output+"completed"
                lines = output.split("\n")
                for l in lines:
                    if l!= "completed" and l!="server1.py":
                        status = os.stat(directory_1+'/'+l)
                        name_file = l
                        l = l + '&' + str(status.st_size) + '&' + str(status.st_mode) + '&' + str(status.st_mtime)
                        if len(recieveds)==3 :
                            if recieveds[1] == "Longlist" and recieveds[2] == "Programmer" and name_file.endswith('.txt'):
                                check_flag = 0

                                with open(name_file) as f:
                                    if "Programmer" in f.read():
                                        check_flag = 1
                                if check_flag == 1:
                                    r2_conn.send(l)
                                    continue
                                else:
                                    continue
                            elif  recieveds[1] == "Longlist" and recieveds[2] != "Programmer"  :
                                r2_conn.send(l)
                                
                        else:
                            r2_conn.send(l)
                            time.sleep(0.01)

                    elif l == "completed":
                        time.sleep(0.1)
                        r2_conn.send("completed")

        
        elif recieveds[0] == "Cache":
            #print "<s1 >",

            if recieveds[1] == "Verify":
                name_file = recieveds[2]
                if os.path.exists(directory_1+'/'+name_file):
                    status = os.stat(directory_1+'/'+name_file)
                    hashvalue = hash_value(directory_1+'/'+name_file)
                    filesize = os.path.getsize(directory_1+'/'+name_file)
                    r2_conn.send(str(filesize)+'&'+str(status.st_mtime)+'&'+hashvalue)
                    progress = tqdm(range(filesize),str("Sending "+name_file), unit="B",unit_scale=False,unit_divisor=1024) 
                
                    length=0
                    with open(name_file,"rb") as f:
                        for _ in progress:
                            bytes_read = f.read(2048)
                            if not bytes_read:
                                break
                            r2_conn.sendall(bytes_read)
                            length+=len(bytes_read)
                            progress.update(len(bytes_read))
                            if length==filesize:
                                break
                        progress.close()
   #                 print("reached")
                    prompt_time=1


                else:
                    r2_conn.send("WRONG") 


              
    


   
