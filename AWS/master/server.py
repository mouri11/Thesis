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