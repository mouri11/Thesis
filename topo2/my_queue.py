import os

src_file = './queue.txt'
dest_file = './master.txt'

while True:
    if os.stat(dest_file).st_size == 0 and os.stat(src_file).st_size > 0:
        f = open(src_file,'r')
        lines = f.readlines()
        f.close()
        f = open(src_file,'w')
        f.writelines((lines[1:]))
        f.close()
        f = open(dest_file,'a')
        f.write(lines[0])
        f.close()