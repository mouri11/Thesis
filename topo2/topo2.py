#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.util import dumpNodeConnections,pmonitor
from mininet.log import setLogLevel
from time import sleep,time
import subprocess
import random
import math
import threading
from multiprocessing import Process,current_process
import os,sys

class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."

    def build(self, n=2):
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            name = 'h' + str(h + 1)
            host = self.addHost(name)
            self.addLink(host, switch)


master_q = []
active_q = []
standby_q = []
free_q = []
dead_q = []

hosts = {}
threads = {}
thread_flag = {}

def print_hosts(n,k):

    file = 'print_out.txt'

    while True:
        if thread_flag['print']['print'] == False:
            return

        orig_stdout = sys.stdout
        f = open(file,'w')
        sys.stdout = f

        print ''
        fmt = '{:<6} {:<7} {:<8} {:<16} {:<18}'
        print fmt.format('Hosts','Status','Action','Added at','Associated Nodes')
        for i in range(n+k):
            name = 'h' + str(i + 1)
            print fmt.format(hosts[name]['name'],hosts[name]['status'],hosts[name]['action'],hosts[name]['uptime'],hosts[name]['assoc_node'])


        fmt2 = '{:<10} {:<10}'
        print fmt2.format('master: ',master_q)
        print fmt2.format('active: ',active_q)
        print fmt2.format('standby: ',standby_q)
        print fmt2.format('dead: ',dead_q)
        print fmt2.format('free: ',free_q)

        # print threads
        print thread_flag

        print ''

        sys.stdout = orig_stdout
        f.close()

        sleep(4)

    thread_flag['print']['print'] = False


def assignStandby(net,interval):
    h1 = net.get('h1')
    file = './master.txt'
    # i = 0
    timer = int(time())
    while True:
        if thread_flag['master']['h1'] == False:
            return

        print 'Inside master thread...:',threading.current_thread().name

        if os.path.isfile(file) and os.stat(file).st_size != 0:
            print 'Handling Node Failure...'

            master_entry = h1.popen('tail -n2 %s' % file).communicate()[0].split('\n')
            
            entry_list = []
            for entry in master_entry:
                if len(entry) > 0:
                    entry_list.append(entry.split(" ")[2:])
                
            entry_list.sort(key=lambda x:x[0])
            print entry_list
            
            h1.cmd('echo >> master_log.txt')
            h1.cmd('echo %s >> master_log.txt' % timer)
            h1.cmd('cat %s >> master_log.txt' % (file))
            open(file,'w').close()

            actv = entry_list[0][2]

            if len(entry_list) == 2:
                while thread_flag[actv][entry_list[0][1]] == True or thread_flag[actv][entry_list[1][1]] == True:
                    print 'Thread not stopped'
                    continue


            threads[actv] = {}
            threads.pop(actv,None)

            active_q.remove(actv)
            dead_q.append(actv)
            hosts[actv]['status'] = 'DEAD'
            hosts[actv]['action'] = 'FREE'
            hosts[actv]['assoc_node'] = []

            # removing failed active node from all standby nodes 
            for host in hosts:
                if hosts[host]['action'] == 'STANDBY' and actv in hosts[host]['assoc_node']:
                    hosts[host]['assoc_node'].remove(actv)

            actv_new = entry_list[0][1]

            node = net.get(actv_new)

            var = node.cmd('tail -n1 %s-comp.txt | awk \'{print $2}\'' % actv).strip()
            print var,type(var)
            # reassigning standby node as new active node
            standby_q.remove(actv_new)
            active_q.append(actv_new)
            hosts[actv_new]['action'] = 'ACTIVE'
            hosts[actv_new]['assoc_node'] = []

            # restarting computation and status announcement
            node.cmd('./compu.sh %s >> %s-comp.txt &' % (var,actv_new))
            node.cmd('./live_status.sh %s %s >> %s-status.txt &' % (actv_new,interval,actv_new))


            # removing new active node from other active nodes
            for host in hosts:
                if hosts[host]['status'] == 'ALIVE' and hosts[host]['action'] == 'ACTIVE' and actv_new in hosts[host]['assoc_node']:
                    hosts[host]['assoc_node'].remove(actv_new)

            print 'After removing from other active nodes....'

            # assigning new free node to standby queue
            if len(free_q) > 0:
                standby_q.insert(0,free_q[0])
                hosts[free_q[0]]['action'] = 'STANDBY'
                free_q.pop(0)

            # ceil(no of active( = 5) * replication factor( = 2) / no . of standby( = 3))
            k = math.ceil(len(active_q) * 2 / len(standby_q))

            # assigning new standby nodes to replace old one, and keep a consistent replication
            i = 0
            for host in hosts:
                if hosts[host]['status'] == 'ALIVE':
                    while hosts[host]['action'] == 'ACTIVE' and len(hosts[host]['assoc_node']) < 2:
                        standby = standby_q[i]
                        i = (i + 1) % len(standby_q)
                        if standby in hosts[host]['assoc_node']: # or len(hosts[standby]['assoc_node']) >= k:
                            continue    
                        hosts[host]['assoc_node'].append(standby)
                        hosts[standby]['assoc_node'].append(host)

            threads[actv_new] = {}
            thread_flag[actv_new] = {}

            for standby in hosts[actv_new]['assoc_node']:
                thread_flag[actv_new][standby] = True

                bg_thread = threading.Thread(target=checkLiveStatus,args=(net,actv_new,standby,interval))
                bg_thread.daemon = True
                bg_thread.start()
                threads[actv_new][standby] = bg_thread

            # print 'Changing hosts...'

            # print_hosts(8,2)
            # break
        # i += 1
        # if i >= 15:
        #     break
        sleep(interval)

    thread_flag['master']['h1'] = False

    print 'Ending master thread...:',threading.current_thread().name


def checkLiveStatus(net,actv,standby,interval):
    print 'Starting...:',threading.current_thread().name

    node = net.get(standby)
    file = actv + '-status.txt'
    timeout = 2 * interval

    i = 0
    while True:
        if thread_flag[actv][standby] == False:
            return

        if os.path.isfile(file) and os.stat(file).st_size != 0:
            timestamp,error = node.popen('tail -n1 %s' % file).communicate()
            timestamp = timestamp.split(" ")[0]
            # print timestamp.strip()
            if timestamp != '' and (int(timestamp) + timeout < int(time())):
                break
            # i += 1
            # sleep(interval)
            # if i >= 15:
            #     return

    h1 = net.get('h1')
    node.cmd('python client.py -i %s -m "%s %s %s"' % (h1.IP(),str(time()),standby,actv)) # .communicate()

    # threads[actv] = {}
    # if actv in active_q:
    #     active_q.remove(actv)
    # if actv not in dead_q:
    #     dead_q.append(actv)
    # hosts[actv]['status'] = 'DEAD'
    # hosts[actv]['action'] = 'FREE'
    # hosts[actv]['assoc_node'] = []

    thread_flag[actv][standby] = False
    print 'Ending...:',threading.current_thread().name


def simpleTest(n,k):
    """Create and test a simple network"""
    topo = SingleSwitchTopo(n)
    net = Mininet(topo)
    net.start()
    print "Starting test..."

    for i in range(n):
        name = 'h' + str(i + 1)
        hosts[name] = {}
        hosts[name]['name'] = name
        hosts[name]['status'] = 'ALIVE'
        hosts[name]['action'] = 'FREE'
        hosts[name]['assoc_node'] = []
        hosts[name]['uptime'] = math.ceil(time())
        free_q.append(name)

    s1 = net.get('s1')

    print 'Adding %d new hosts...' % k
    for i in range(n + 1,n + k + 1):
        name = 'h' + str(i)
        host = net.addHost(name)
        net.addLink(host,s1)
        s1.attach('s1-eth%s' % i)
        host.cmd('ifconfig h%s-eth0 10.%s' % (i,i))
        hosts[name] = {}
        hosts[name]['name'] = name
        hosts[name]['status'] = 'ALIVE'
        hosts[name]['action'] = 'FREE'
        hosts[name]['assoc_node'] = []
        hosts[name]['uptime'] = math.ceil(time())
        free_q.append(name)

    interval = 2

    print 'Setting up cluster...'
    hosts['h1']['action'] = 'MASTER'
    free_q.remove('h1')
    master_q.append('h1')
    h1 = net.get('h1')
    h1.cmd('python server.py -i %s &' % h1.IP())
    # master_thread = threading.Thread(target=assignStandby,args=(net,interval))

    open('print_out.txt','w').close()
    file_list = h1.cmd('ls | grep ^h').splitlines()
    # print file_list
    if os.path.isfile('./master.txt'):
        os.remove('./master.txt')

    if file_list != []:
        for file in file_list:
            os.remove(os.path.join('./',file))

    for i in range(2,7):
        actv = 'h' + str(i)
        free_q.remove(actv)
        hosts[actv]['action'] = 'ACTIVE'
        active_q.append(actv)
        node = net.get(actv)
        var = 10895
        node.cmd('./compu.sh %s >> %s-comp.txt &' % (var,actv))
        node.cmd('./live_status.sh %s %s >> %s-status.txt &' % (actv,interval,actv))

    for i in range(7,10):
        standby = 'h' + str(i)
        free_q.remove(standby)
        standby_q.append(standby)
        hosts[standby]['action'] = 'STANDBY'

    i = 0
    for actv in active_q:
        threads[actv] = {}
        thread_flag[actv] = {}

        while len(hosts[actv]['assoc_node']) < 2:
            standby1 = standby_q[i]
            i = (i + 1) % len(standby_q)
            hosts[actv]['assoc_node'].append(standby1)
            hosts[standby1]['assoc_node'].append(actv)
            # bg_thread = threading.Thread(target=checkLiveStatus,args=(net,actv,standby1,interval))
            thread_flag[actv][standby1] = True

            bg_thread = threading.Thread(target=checkLiveStatus,args=(net,actv,standby1,interval))
            bg_thread.daemon = True
            bg_thread.start()
            threads[actv][standby1] = bg_thread

    thread_flag['master'] = {}
    thread_flag['master']['h1'] = True

    master_thread = threading.Thread(target=assignStandby,args=(net,interval))
    master_thread.daemon = True
    master_thread.start()
    threads['master'] = {}
    threads['master']['h1'] = master_thread
    # print threads

    thread_flag['print'] = {}
    thread_flag['print']['print'] = True

    print_thread = threading.Thread(target=print_hosts,args=(n,k))
    print_thread.daemon = True
    print_thread.start()
    threads['print'] = {}
    threads['print']['print'] = print_thread

    print_process = subprocess.Popen(args=["lxterminal","--geometry=80x35+160+0", "--command=./printer.sh %s %s" % ((n+k+10),2)])

    sleep(7)
    host = net.get('h2')
    print host.IP()
    # rand = math.ceil(random.random() * 10000000)
    # if rand % 2:
    host.stop(deleteIntfs=True)
    host.terminate()
    net.hosts.remove(host)
    del net.nameToNode[host.name]

    # sleep(7)
    # host = net.get('h4')
    # print host.IP()
    # host.stop(deleteIntfs=True)
    # host.terminate()
    # net.hosts.remove(host)
    # del net.nameToNode[host.name]

    CLI(net)

    print 'Stopping background processes...'
    # thread_flag['print']['print'] = False

    for actv in threads:
        for standby in threads[actv]:
            # for standby in actv:
            thread_flag[actv][standby] = False
            threads[actv][standby].join()
    
    net.stop()

    print_process.terminate()
    process = subprocess.Popen("sudo mn -c".split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print output,error

if __name__ == '__main__':
    # Tell mininet to print useful information
    # open('output.txt','w').close()
    setLogLevel('info')
    simpleTest(8,2)