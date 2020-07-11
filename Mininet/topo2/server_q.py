import socket, optparse, os
import threading

parser = optparse.OptionParser()
parser.add_option('-i',dest='ip',default='')
parser.add_option('-p',dest='port',type='int',default=12345)
(options,args) = parser.parse_args()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((options.ip, options.port))

filename = "master.txt"

queue = []

def addToQueue():
    while True:
        data, addr = s.recvfrom(512)
        queue.append((addr,data))

def writeToFile():
    while True:
        f = open(filename,'a')
        if os.stat(filename).st_size == 0 and len(queue) > 0:
            addr = queue[0][0]
            data = queue[0][1]
            queue.pop(0)
            f.write("%s: %s\n" % (addr,data))
            f.flush()
            print data,addr
        f.close()

if __name__ == '__main__':
    print 'Starting server...'

    thread = threading.Thread(target=addToQueue)
    thread.daemon = True
    thread.start()

    thread2 = threading.Thread(target=writeToFile)
    thread2.daemon = True
    thread2.start()

    thread.join()
    thread2.join()
