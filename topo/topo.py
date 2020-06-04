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
    # os.remove('./master.txt')

    # if file_list != []:
    #     for file in file_list:
    #         os.remove(os.path.join('./',file))

    interval = 8

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

    # pid = []

        # result = node.cmd('ping -i %s 10.%s;echo $?' % (interval,hosts[host]['assoc_node'][1:])).splitlines()
        # _PID = node.cmd('ps aux | grep \"10.%s\" | awk \'{print $2}\'' % hosts[host]['assoc_node'][1:])
        # pid.push(_PID)


    # for host in standby_q:
    # h1.cmd('./pinging.sh 10.2 2 >> h2.txt &')
    # # print result
    # sleep(10)
    # h2 = net.get('h2')
    # h2.stop()
    # h2.terminate()

    # for i in range(4):
        # for host in standby_q:
        #     node = net.get(host)
        #     assoc_node = hosts[host]['assoc_node']
            # if assoc_node in active:
            # result = node.cmd('ping -c1 10.%s;echo $?' % assoc_node[1:]).splitlines()
            # if result[-1] == 2:
            #     continue
            # print result
            # node.cmd('echo \"' + str(time()) + ' ' + assoc_node + ' ' + result[-1] + '\" >> ' + host + '.txt')

        # sleep(4)
        # dead = random.choice(active_q)
        # if dead in net.hosts:

    # print 'active: ',active_q
    # print 'standby: ',standby_q
    # print 'dead: ',dead_q
    # print 'free: ',free_q
     
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
                # print h1.cmd('ping -c1 %s;echo $?' % host.IP())
                # hosts[dead]['status'] = 'DEAD'
                # hosts[dead]['action'] = 'FREE'
                # hosts[dead]['assoc_node'] = []
                # active_q.remove(dead)

    # for p in threads:
    #     p.join()

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

    # print hosts

    # for i in range(1,n + 1):
    #     host = net.get('h%d' % (i))
    #     s = 'echo "h' + str(i) + ' `hostname -I`" >> output.txt'
    #     # print s
    #     result = host.cmd(s)
    #     # print result
    
    # s1 = net.get('s1')
    # h1 = net.get('h1')
    # h2 = net.get('h2')
    # h3 = net.get('h3')
    # h4 = net.get('h4')
    # for i in range(n + 1,n + k + 1):
	   #  host = net.addHost('h%s' % i)
	   #  net.addLink(host,s1)
	   #  s1.attach('s1-eth%s' % i)
	   #  host.cmd('ifconfig h%s-eth0 10.%s' % (i,i))
	   #  host.cmd('echo "h' + str(i) + ' `hostname -I`" >> output.txt')
	   #  result = h1.cmd('ping -c1 10.%s;echo $?' % i)
	   #  # net.delHost(host)
	   #  print result

    # h1.cmd('python server.py -i %s &' % h1.IP())
    # h3.cmd('python server.py -i %s &' % h3.IP())
    # h4.cmd('python server.py -i %s &' % h4.IP())
    # PID = h2.cmd('ps aux | grep "server.py" | grep -v grep | awk \'{print $2}\'').splitlines()
    # print PID
    # h2.cmd('python client.py -i %s -m "Hello World"' % h1.IP())
    # print "Dumping host connections"
    # dumpNodeConnections(net.hosts)
    # print "Testing network connectivity"
    # net.pingAll()
    
    # p1.terminate()
    # h2.cmd('kill -9 %s' % PID)
    # for no in PID:
    #     h2.cmd('kill -9 %s' % no)
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