#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from time import sleep,time
import subprocess
import random
import math
import threading
# from multiprocessing import Process
import os

class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."

    def build(self, n=2):
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            name = 'h' + str(h + 1)
            host = self.addHost(name)
            self.addLink(host, switch)

# def allotStandbyNode(net,hosts,queues):



def checkIfAlive(net,hosts,standby,interval,queues):
    node = net.get(standby)
    actv = hosts[standby]['assoc_node'][0]
    file = standby + '-2-' + actv + '.txt'
    # file = actv + '-fail.txt'
    # print file
    while True:
        # sleep(interval)
        result = node.cmd('tail -n1 %s | awk \'{print $3}\'' % (file)).strip()
        # print result,type(result)
        if os.stat(file).st_size != 0 and result == "1": # if os.path.isfile(file) and os.stat(file).st_size != 0:
            break
        sleep(interval)

    h1 = net.get('h1')
    node.cmd('python client.py -i %s -m "%s %s %s"' % (h1.IP(),str(math.ceil(time())),standby,actv))

    node.cmd('./compu.sh $(tail -n1 %s-comp.txt | awk \'{print $2}\') >> %s-comp.txt &' % (actv,standby))

    hosts[standby]['action'] = 'ACTIVE'
    hosts[standby]['assoc_node'] = []
    hosts[actv]['status'] = 'DEAD'
    hosts[actv]['action'] = 'FREE'
    hosts[actv]['assoc_node'] = []
    active_q = queues[0]
    standby_q = queues[1]
    dead_q = queues[2]
    free_q = queues[3]
    active_q.remove(actv)
    active_q.append(standby)
    standby_q.remove(standby)
    dead_q.append(actv)
    if standby in free_q:
        free_q.remove(standby)

def simpleTest(n,k):
    """Create and test a simple network"""
    topo = SingleSwitchTopo(n) # TreeTopo(2,2)
    net = Mininet(topo)
    net.start()
    print "Starting test..."

    active_q = []
    standby_q = []
    free_q = []
    dead_q = []
    threads = []

    hosts = {}

    fmt = '{:<4} {:<5} {:<8} {:<16} {:<16}'

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

        # host.cmd('echo "h' + str(i) + ' `hostname -I`" >> output.txt')
        # result = h1.cmd('ping -c1 10.%s;echo $?' % i)
        # net.delHost(host)
        # print result

    print 'Setting up cluster...'
    hosts['h1']['action'] = 'MASTER'
    h1 = net.get('h1')
    h1.cmd('python server.py -i %s &' % h1.IP())

    file_list = h1.cmd('ls | grep ^h').splitlines()
    # print file_list
    os.remove('./master.txt')

    if file_list != []:
        for file in file_list:
            os.remove(os.path.join('./',file))

    interval = 10

    for i in range(1,n,2):
        actv = 'h' + str(i + 1)
        standby = 'h' + str(i + 2)
        free_q.pop(0)
        free_q.pop(0)

        hosts[actv]['action'] = 'ACTIVE'
        hosts[actv]['assoc_node'].append(standby)
        active_q.append(actv)
        node = net.get(actv)
        var = 10895
        node.cmd('./compu.sh %s >> %s-comp.txt &' % (var,actv))

        # bg_thread = threading.Thread(target=doComputation,args=(net,actv))
        # bg_thread.start()
        # threads.append(bg_thread)

        hosts[standby]['action'] = 'STANDBY'
        hosts[standby]['assoc_node'].append(actv)
        standby_q.append(standby)
        node = net.get(standby)
        # node.cmd('./pinging.sh 10.%s %s %s %s >> %s-2-%s.txt &' % (actv[1:],interval,str(time()),actv,standby,actv))
        # bg_thread = threading.Thread(target=checkIfAlive,args=(net,hosts,standby,interval,[active_q,standby_q,dead_q]))
        # bg_thread.start()
        # threads.append(bg_thread)

        # standby = net.get(host2)
        # result = standby.cmd('ping -c1 10.%s;echo $?' % (i + 1))
        # print result.splitlines()[-1]

    for host in standby_q:
        node = net.get(host)
        # interval = 2
        assoc_node = hosts[host]['assoc_node']
        for actv in assoc_node:
            node.cmd('./pinging.sh 10.%s %s %s >> %s-2-%s.txt &' % (actv[1:],interval,actv,host,actv))
    #         # result = node.cmd('tail -n1 %s-2-%s.txt | awk \'{print $3}\'' % (host,actv))
    #         # print result
            bg_thread = threading.Thread(target=checkIfAlive,args=(net,hosts,host,interval,[active_q,standby_q,dead_q,free_q]))
            bg_thread.daemon = True
            bg_thread.start()
            threads.append(bg_thread)

    for i in range(n+k):
        name = 'h' + str(i + 1)
        print fmt.format(hosts[name]['name'],hosts[name]['status'],hosts[name]['action'],hosts[name]['assoc_node'],hosts[name]['uptime'])


    fmt2 = '{:<10} {:<10}'
    print fmt2.format('active: ',active_q)
    print fmt2.format('standby: ',standby_q)
    print fmt2.format('dead: ',dead_q)
    print fmt2.format('free: ',free_q)
     
    temp = active_q[:]
    length = len(temp)
    for i in range(length):
        dead = random.choice(temp)
        host = net.get(dead)
        print host.IP()
        # rand = math.ceil(random.random() * 10000000)
        # if rand % 2:
        host.stop(deleteIntfs=True)
        host.terminate()
        net.hosts.remove(host)
        del net.nameToNode[host.name]
        temp.remove(dead)
        filename = dead + '-fail.txt'
        msg = dead + " failed at " + str(math.ceil(time()))
        f = open(filename,"a")
        f.write(msg)
        f.close()
        sleep(4)

    for t in threads:
        t.join()

    print ""
    for i in range(n+k):
        name = 'h' + str(i + 1)
        print fmt.format(hosts[name]['name'],hosts[name]['status'],hosts[name]['action'],hosts[name]['assoc_node'],hosts[name]['uptime'])

    print fmt2.format('active: ',active_q)
    print fmt2.format('standby: ',standby_q)
    print fmt2.format('dead: ',dead_q)
    print fmt2.format('free: ',free_q)

    CLI(net)
    net.stop()

    # for thread in threads:


    process = subprocess.Popen("sudo mn -c".split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print output,error

if __name__ == '__main__':
    # Tell mininet to print useful information
    # open('output.txt','w').close()
    setLogLevel('info')
    simpleTest(8,2)