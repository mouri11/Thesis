#!/usr/bin/env python3

import socket,optparse
import time

parser = optparse.OptionParser()
parser.add_option('-i',dest='ip',default='localhost')
parser.add_option('-p',dest='port',type='int',default=12345)
(options,args) = parser.parse_args()

with socket.socket() as s:
    host = options.ip
    port = options.port

    s.bind ((host,port))
    # print(f'socket binded to {port}')
    s.listen()

    file = 'master-stat.txt'
    while True:
        con,addr = s.accept()
        data = con.recv(1024)
        if len(data) <= 0:
            break
        data = data.decode('utf-8')
        #if len(data) != 2:
            #continue
        # print(data,addr)
        f = open(file,'a')
        f.write("%s %s %s\n" % (addr[0],int(time.time()),data))
        f.flush()
        f.close()
ubuntu@ip-172-31-88-99:~$ 
ubuntu@ip-172-31-88-99:~$ cat handler.py 
#!/usr/bin/env python3

import subprocess
from time import sleep

# allocating nodes as active or standby. will do dynamic alloc later
def alloc_nodes():
    file = open('nodes','r')
    nodes = file.readlines()
    file.close()
    print(nodes)

    file1 = open('active','w')
    file1.write(nodes[0])
    file1.close()

    file1 = open('standby','w')
    file1.write(nodes[1])
    file1.close()

# starts appropriate funtions on nodes:
# compu.sh and sendinfo.sh on active
# server.py and timeout.py on standby
def start_nodes(): 
    file = open('standby','r')

    while True:
        line = file.readline().strip()
        if not line:
            break
        line = line.split("    ")
        ip = line[1].strip()
        cmd = 'ssh ' + ip + ' ./server.py -i 0.0.0.0 > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        #cmd = 'ssh ' + ip + ' ./killer.sh ./server.py'
        #subprocess.run(cmd.split(" "))
    
    file.close()

    # for active nodes
    file = open('active','r')

    while True:
        line = file.readline().strip()
        if not line:
            break
        line = line.split("    ")
        ip = line[1].strip()
        cmd = 'ssh ' + ip + ' ./compu.sh 10895 > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
    #    sleep(10)
        cmd = 'ssh ' + ip + ' ./sendinfo.sh > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))

    file.close()

    file = open('standby','r')

    while True:
        line = file.readline().strip()
        if not line:
            break
        line = line.split("    ")
        ip = line[1].strip()
        cmd = 'ssh ' + ip + ' ./timeout.py > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        #cmd = 'ssh ' + ip + ' ./killer.sh ./server.py'
        #subprocess.run(cmd.split(" "))
    
    file.close()

def stop_nodes():
    file = open('active','r')

    while True:
        line = file.readline().strip()
        if not line:
            break
        line = line.split("    ")
        ip = line[1].strip()
        cmd = 'ssh ' + ip + ' ./killer.sh ./compu.sh > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        cmd = 'ssh ' + ip + ' ./killer.sh ./sendinfo.sh'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
    
    file.close()
    
    file = open('standby','r')

    while True:
        line = file.readline().strip()
        if not line:
            break
        line = line.split("    ")
        ip = line[1].strip()
        #cmd = 'ssh ' + ip + ' ./killer.sh ./timeout.py > /dev/null 2>&1 &'
        # print(cmd.split(" "))
        #subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        cmd = 'ssh ' + ip + ' ./killer.sh ./server.py'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
    
    file.close()

if __name__ == "__main__":
    cmd = './server.py -i 0.0.0.0 &'
    print("Running ",cmd,"...")
    proc = subprocess.Popen(cmd.split(" "),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    start_nodes()
    sleep(10)
    stop_nodes()
    print("Stopping server...")
    proc.terminate()
    # alloc_nodes()