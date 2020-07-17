#!/usr/bin/env python3

import subprocess
from time import sleep
import os

master_q = []
active_q = []
standby_q = []
free_q = []
dead_q = []

hosts = {}

def failure_handling():
    queue_file = 'master-stat.txt'

    while True:
        if not os.path.isfile(queue_file) or os.stat(queue_file).st_size == 0:
            continue
        file1 = open(queue_file,'r')
        line = file1.readline()
        file1.close()

        file2 = open(queue_file,'w')
        file2.write(subprocess.run(['tail','-n','+2',queue_file],stdout=subprocess.PIPE).stdout.decode('utf-8'))
        file2.close()

        file3 = open('master-log.txt','a')
        file3.write(line)
        file3.close()

        line = line.strip().split(" ")[-1].split("...")
        active = line[1]
        standby = line[0]
        
        if hosts[active]['status'] == 'DEAD':
            contine

        for node in hosts[active]['assoc_node']:
            hosts[node]['assoc_node'].remove(active)
        
        active_q.remove(active)
        dead_q.append(active)
        hosts[active]['status'] = 'DEAD'
        hosts[active]['action'] = 'FREE'
        hosts[active]['assoc_node'] = []

        cmd = 'ssh ' + hosts[standby]['IP'] + ' ./killer.sh ./timeout.py'
        print('Running ',cmd,'...')
        subprocess.run(cmd.split(" "))
        cmd = 'ssh ' + hosts[standby]['IP'] + ' ./killer.sh ./server.py'
        print('Running ',cmd,'...')
        subprocess.run(cmd.split(" "))

        standby_q.remove(standby)
        active_q.append(standby)
        hosts[standby]['action'] = 'ACTIVE'
        hosts[standby]['assoc_node'] = []

        free_len = len(free_q)
        if len(free_q) > 0:
            standby_q.append(free_q[0])
            cmd = 'ssh ' + hosts[free_q[0]]['IP'] + ' ./server.py -i 0.0.0.0 > /dev/null 2>&1 &'
            print("Running ",cmd,'...')
            subprocess.run(cmd.split(" "))
            hosts[free_q[0]]['action'] = 'STANDBY'
            free_q.pop(0)

        if len(standby_q) == 0:
            print('*** ALERT ***')
            print('No standby nodes available')
            break

        changed = []
        i = 0
        for host in hosts:
            if hosts[host]['status'] == 'ALIVE' and hosts[host]['action'] == 'ACTIVE':
                while True:
                    if len(standby_q) == 1 and len(hosts[host]['assoc_node']) >= 1:
                        break
                    elif len(hosts[host]['assoc_node']) == 2:
                        break

                    _standby = standby_q[i]
                    i = (i + 1) % len(standby_q)
                    if _standby in hosts[host]['assoc_node']:
                        continue
                    if host not in changed:
                        changed.append(host)
                    if _standby not in changed:
                        changed.append(_standby)

                    hosts[host]['assoc_node'].append(_standby)
                    hosts[_standby]['assoc_node'].append(host)

                    if len(standby_q) == 1:
                        break

        for host in changed:
            if hosts[host]['status'] == 'ALIVE' and hosts[host]['action'] in ['ACTIVE','STANDBY']:
                node_file = ""
                if hosts[host]['action'] == 'ACTIVE':
                    node_file = 'standby'
                else:
                    node_file = 'active'

                cmd = 'rm ' + node_file
                print('Running ',cmd,'...')
                subprocess.run(cmd.split(" "))
                file1 = open(node_file,'a')
                for node in hosts[host]['assoc_node']:
                    file1.write("%s    %s\n" % (node,hosts[node]['IP']))
                file1.close()

                cmd = 'rsync ' + node_file + ' ' + hosts[host]['IP'] + ':~/'
                print("Running ",cmd,'...')
                subprocess.run(cmd.split(" "))

                if node_file == 'active':
                    cmd = 'rsync master ' + hosts[host]['IP'] + ':~/'
                    print('Running ',cmd,'...')
                    subprocess.run(cmd.split(" "))


        cmd = 'ssh ' + hosts[standby]['IP'] + ' tail -n1 ' + active + '-comp.txt | awk \'{print $2}\''
        val = subprocess.run(cmd.split(" "),stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        cmd = 'ssh ' + hosts[standby]['IP'] + ' ./compu.sh ' + val + ' > /dev/null 2>&1 &'
        subprocess.run(cmd.split(" "))
        cmd = 'ssh ' + hosts[standby]['IP'] + ' ./sendinfo.sh > /dev/null 2>&1 &'
        print('Running ',cmd,'...')
        subprocess.run(cmd.split(" "))

        if len(free_q) != free_len:
            cmd = 'ssh ' + hosts[standby_q[-1]]['IP'] + ' ./timeout.py > /dev/null 2>&1 &'
            print('Running ',cmd,'...')
            subprocess.run(cmd.split(" "))

        if len(standby_q) == 0:
            break

# allocating nodes as active or standby. will do dynamic alloc later
def alloc_nodes(n,k):
    file = open('nodes','r')
    nodes = file.readlines()
    file.close()
    print(nodes)

    for node in nodes:
        node = node.strip().split("    ")
        name = node[0].strip()
        hosts[name] = {}
        hosts[name]['IP'] = node[1].strip()
        hosts[name]['status'] = 'ALIVE'
        hosts[name]['action'] = 'FREE'
        hosts[name]['assoc_node'] = []
        free_q.append(name)

    for i in range(n):
        hosts[free_q[0]]['action'] = 'ACTIVE'
        active_q.append(free_q[0])
        free_q.pop(0)

    for i in range(n):
        hosts[free_q[0]]['action'] = 'STANDBY'
        standby_q.append(free_q[0])
        free_q.pop(0)

    i = 0
    k = 1
    for actv in active_q:
        for j in range(k):
            hosts[actv]['assoc_node'].append(standby_q[i])
            hosts[standby_q[i]]['assoc_node'].append(actv)
            i = (i + 1) % len(standby_q)

    hostname = subprocess.run('uname -n'.split(" "),stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    ip = subprocess.run('hostname -I'.split(" "),stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
    
    if not os.path.exists('./master') or os.stat('./master').st_size == 0:
        file = open('master','w')
        file.write("%s    %s\n" % (hostname,ip))
        file.close()


    for actv in active_q:
        file = open('standby','w')
        for node in hosts[actv]['assoc_node']:
            file.write("%s    %s\n" % (node,hosts[node]['IP']    ))

        file.close()
        cmd = 'rsync standby ' + hosts[actv]['IP'] + ':~/'
        print('Running ',cmd,'...')
        subprocess.run(cmd.split(" "))

    for stndby in standby_q:
        file = open('active','w')
        for node in hosts[stndby]['assoc_node']:
            file.write("%s    %s\n" % (node,hosts[node]['IP']    ))

        file.close()
        cmd = 'rsync active ' + hosts[stndby]['IP'] + ':~/'
        print('Running ',cmd,'...')
        subprocess.run(cmd.split(" "))
        cmd = 'rsync master ' + hosts[stndby]['IP'] + ':~/'
        print('Running ',cmd,'...')
        subprocess.run(cmd.split(" "))


    #active = active_q[0]
    #standby = standby_q[0]
    #hosts[active]['assoc_node'].append(standby)
    #hosts[standby]['assoc_node'].append(active)

    #file1 = open('active','w')
    #file1.write(nodes[0])
    #file1.close()

    #file1 = open('standby','w')
    #file1.write(nodes[1])
    #file1.close()

# starts appropriate funtions on nodes:
# compu.sh and sendinfo.sh on active
# server.py and timeout.py on standby
def start_nodes(): 
    # file = open('standby','r')

    #while True:
    for standby in standby_q:
        #line = file.readline().strip()
        #if not line:
            #break
        #line = line.split("    ")
        ip = hosts[standby]['IP']
        cmd = 'ssh ' + ip + ' ./server.py -i 0.0.0.0 > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        #cmd = 'ssh ' + ip + ' ./killer.sh ./server.py'
        #subprocess.run(cmd.split(" "))
    
    #file.close()

    # for active nodes
    #file = open('active','r')

    #while True:
    for active in active_q:
        #line = file.readline().strip()
        #if not line:
            #break
        #line = line.split("    ")
        ip = hosts[active]['IP'] #line[1].strip()
        cmd = 'ssh ' + ip + ' ./compu.sh 10895 > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
    #    sleep(10)
        cmd = 'ssh ' + ip + ' ./sendinfo.sh > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))

    #file.close()

    #file = open('standby','r')

    #while True:
    for standby in standby_q:
        #line = file.readline().strip()
        #if not line:
            #break
        #line = line.split("    ")
        ip = hosts[standby]['IP'] #line[1].strip()
        cmd = 'ssh ' + ip + ' ./timeout.py > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        #cmd = 'ssh ' + ip + ' ./killer.sh ./server.py'
        #subprocess.run(cmd.split(" "))
    
    #file.close()

def stop_nodes():
    #file = open('active','r')

    #while True:
    for active in active_q:
        #line = file.readline().strip()
        #if not line:
        #    break
        #line = line.split("    ")
        ip = hosts[active]['IP'] #line[1].strip()
        cmd = 'ssh ' + ip + ' ./killer.sh ./compu.sh > /dev/null 2>&1 &'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        cmd = 'ssh ' + ip + ' ./killer.sh ./sendinfo.sh'
        print("Running ",cmd,"...")
        subprocess.run(cmd.split(" "))
    
    #file.close()
    
    #file = open('standby','r')

    #while True:
    #for standby in standby_q:
        #line = file.readline().strip()
        #if not line:
        #    break
        #line = line.split("    ")
        #ip = hosts[standby]['IP']
        #cmd = 'ssh ' + ip + ' ./killer.sh ./timeout.py > /dev/null 2>&1 &'
        # print(cmd.split(" "))
        #subprocess.run(cmd.split(" "))
        #print(proc.pid)
        #sleep(10)
        #cmd = 'ssh ' + ip + ' ./killer.sh ./server.py'
        #print("Running ",cmd,"...")
        #subprocess.run(cmd.split(" "))
    
    #file.close()

if __name__ == "__main__":
    cmd = './server.py -i 0.0.0.0 &'
    print("Running ",cmd,"...")
    proc = subprocess.Popen(cmd.split(" "),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    alloc_nodes(1,1)
    start_nodes()
    failure_handling()
    #sleep(10)
    #stop_nodes()
    #print("Stopping server...")
    #proc.terminate()
