#!/usr/bin/env python3

import time
from time import sleep
import subprocess,threading

def checkIfAlive(active,interval):
    cmd = 'uname -n'
    standby = subprocess.run(cmd.split(" "),stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    file1 = open('master','r')
    master = file1.readline().split("    ")[1].strip()
    file1.close()

    file = active + "-stat.txt"
    while True:
        result = subprocess.run(['tail','-n2',file],stdout=subprocess.PIPE).stdout.decode('utf-8')
        # print(result)
        result = result.split("\n")
        result.pop(-1)
        timeout = 2
        alive1 = int(result[0].split(" ")[0].strip())
        if len(result) >= 2:
            alive2 = int(result[1].split(" ")[0].strip())
            if abs(int(time.time() - alive2) > abs(alive2 - alive1 + interval + timeout)):
                cmd = './client.py -i ' + master  + ' -m ' + standby + '...' + active
                print(cmd.split(" "))
                subprocess.run(cmd.split(" "))
                print(active + " is dead!!2 "+ str(int(time.time())))
                file1 = open(active+'-death.txt','a')
                file1.write(str(int(time.time())) + ' death\n')
                file1.close()
                return
        else:
            if abs(int(time.time()) - alive1) > (interval + 2 * timeout):
                cmd = './client.py -i ' + master  + ' -m ' + standby + '...' + active
                subprocess.run(cmd.split(" "))
                print(active + " is dead!!1" + str(int(time.time())))
                file1 = open(active+'-death.txt','a')
                file1.write(str(int(time.time())) + ' death\n')
                file1.close()
                return
        print(active + " is alive :/" + str(int(time.time())))
        sleep(interval)

# checkIfAlive("ip-172-31-90-221")
if __name__ == "__main__":
    threads = []
    file = open("active",'r')
    while True:
        line = file.readline()
        # print("line:",line)
        if len(line) <= 0:
            break
        active = line.split("    ")[0]
        # print(active)
        bg_thread = threading.Thread(target=checkIfAlive,args=(active,2))
        bg_thread.daemon = True
        bg_thread.start()
        threads.append(bg_thread)

    file.close()

    for thread in threads:
        thread.join()