# Copyright 2018 Inria Damien.Saucez@inria.fr
#
#   Permission to use, copy, modify, and/or distribute this software for any
#   purpose with or without fee is hereby granted, provided that the above
#   copyright notice and this permission notice appear in all copies.
#
#   THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
#   REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
#   AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
#   INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
#   LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
#   OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
#   PERFORMANCE OF THIS SOFTWARE.

k = 4

login = "login"
password = "password"
subnet = "10.0.0.0/8"

location = "nancy"
walltime = "1:00"

images = {
        "ovs":"file:///home/dsaucez/distem-fs-jessie-ovs.tar.gz",
        "hadoop-slave":"file:///home/dsaucez/slave.tgz",
        "hadoop-master":"file:///home/dsaucez/master.tgz",
        }

# == store
masters = list()
slaves = list()

# == Helper variables ========================================================
k2 = int( k/2 )

# == Helper functions ========================================================
def coreName(seq):
    return "Core-%d" % (seq)

def aggrName(pod, seq):
    return "Aggr-%d-%d" % (pod, seq)

def edgeName(pod, seq):
    return "Edge-%d-%d" % (pod, seq)

def hostName(pod, edge, seq):
    return "Host-%d-%d-%d" % (pod, edge, seq)

def addSwitch(name):
    image = images["ovs"]
    print('o.add_switch("%s", image="%s")' % (name, image))

def addNode(name, role): 
    image = images[role]
    print ('o.add_node("%s", image="%s")' %(name, image))

def addLink(a, b):
    print('o.add_link("%s", "%s")' % (a, b))

def upload_array_as_file(host, name, lines, clean = False):
    # remove first the file
    if clean:
        cmd = "rm -f %s" %(name)
        print ('o.execute_command("%s", "%s")' % (host, cmd))
    
    for line in lines:
        cmd = 'echo "%s" >> %s' % (line, name)
        print ('o.execute_command("%s", "%s")' % (host, cmd))

def getIp(name):
    return "1.2.3.4"#nodes[name]["ip"]

# Define all slaves
def make_slaves_file(slaves, masters):
    for host in slaves + masters:
        print ("\n#slaves on", host)
        upload_array_as_file(host, "/root/hadoop-2.7.6/etc/hadoop/slaves", slaves, True)


# Define all masters
def make_masters_file(masters):
    for host in masters:
        print ("\n#masters on", host)
        upload_array_as_file(host, "/root/hadoop-2.7.6/etc/hadoop/masters", masters, True)

# Build /etc/hosts
def makeHostsFile(nodes):
    hosts_file = ["127.0.0.1\tlocalhost localhost.locadomain"]
    for node in nodes:
        hosts_file.append("%s\t%s" % (getIp(node), node))
    
    for node in nodes:
        upload_array_as_file(node, "/etc/hosts", hosts_file, False)
        print()

# ============================================================================
print('o = distem("%s", "%s", "%s")' % (login, password, subnet))

# build cores
for seq in range(1, int((k/2)**2)+1):
    corename = coreName(seq)
    addSwitch(corename)
print ("")

# Create Pods
for pod in range(1, k+1):
    print ("\n#Pod %d" % (pod))
    
    # Create aggregation switches
    for aggr in range (1, k2 + 1):
        aggrname = aggrName(pod, aggr)
        addSwitch(aggrname)
       
        # Connect it to the core switches
        for i in range(1, k2+1):
            coreid = (i-1) * k2 + aggr 
            corename = coreName(coreid)
            addLink(aggrname, corename)
        print()
    print()

    # Create edge switches
    for edge in range(1, k2 + 1):
        edgename = edgeName(pod, edge)
        addSwitch(edgename)

        # Connect it to the aggregation switches
        for aggr in range(1, k2 + 1):
            addLink(edgename, aggrName(pod, aggr))

        # Create hosts
        print ("")
        for host in range(1, k2 + 1):
            hostname = hostName(pod, edge, host)
            role = "hadoop-slave"
            if host == 1 and pod == 1 and edge == 1:
                role = "hadoop-master"
                masters.append(hostname)
            else:
                slaves.append(hostname)

            addNode(hostname, role=role)
            # Connect it to the edge switch
            addLink(hostname, edgename)
        print()

print ()
################### hosts_file.append("%s\t%s" %(get_ip(name), name))

# Create and upload /etc/hosts
print ("\n# Upload /etc/hosts")
makeHostsFile(nodes=masters+slaves)

# Setup the slaves file
print ("\n# Upload etc/hadoop/slaves")
make_slaves_file(slaves=slaves, masters=masters)

# Setup the masters file
print ("\n# Upload etc/hadoop/masters")
make_masters_file(masters=masters)

# Let's deploy
print ("\n# Deploy the experiment")
print('o.reserve("%s", walltime="%s")' % (location, walltime ))
print("o.deploy()")
