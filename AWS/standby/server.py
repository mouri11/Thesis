#!/usr/bin/env python3

import socket,optparse
import time
import subprocess

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

    file = '-stat.txt'
    while True:
        con,addr = s.accept()
        data = con.recv(1024)
        if len(data) <= 0:
            break
        hostname = subprocess.run(['./get-ip.sh',addr[0]],stdout=subprocess.PIPE).stdout
        hostname = hostname.decode('utf-8').strip()
        data = data.decode('utf-8').strip()
        f = open(hostname+file,'a')
        f.write("%s %s\n" % (int(time.time()),data))
        f.flush()
        f.close()