import socket,optparse

parser = optparse.OptionParser()
parser.add_option('-i',dest='ip',default='127.0.0.1')
parser.add_option('-p',dest='port',type='int',default=12345)
parser.add_option('-m',dest='msg')
(options,args) = parser.parse_args()

if not options.msg:
    print("Empty message!!")
    exit()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    host = options.ip
    port = options.port

    s.connect((host,port))
    s.sendall(bytes(str(options.msg),'utf-8'))
    # print(str(s.recv(4096),'utf-8'))
