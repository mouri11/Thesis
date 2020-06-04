import socket, optparse

parser = optparse.OptionParser()
parser.add_option('-i',dest='ip',default='')
parser.add_option('-p',dest='port',type='int',default=12345)
(options,args) = parser.parse_args()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((options.ip, options.port))

filename = 'master' + '.txt'
while True:
    f = open(filename,'a')
    data, addr = s.recvfrom(512)
    print data,addr
    f.write("%s: %s\n" % (addr, data))
    f.flush()
    f.close()