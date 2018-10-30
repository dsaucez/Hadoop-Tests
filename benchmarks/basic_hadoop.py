#Copyright 2018 Inria Damien.Saucez@inria.fr
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

nodes = {
        "switch1":{
            "type":"switch",
            "image":"ovs",
            },
        "slave-1": {
            "type":"host",
            "hadoop-type":"slave",
            "image":"hadoop-slave",
            "ip":"10.0.0.101",
            },
        "slave-2": {
            "type":"host",
            "hadoop-type":"slave",
            "image":"hadoop-slave",
            "ip":"10.0.0.102",
            },
        "host-master":{
            "type":"host",
            "hadoop-type":"master",
            "image":"hadoop-master",
            "ip":"10.0.0.11"
            },
        }

links = [("switch1", "slave-1"), ("switch1", "slave-2"), ("switch1", "node-master")]

images = {
        "hadoop-slave":"file:///home/dsaucez/slave.tgz",
        "hadoop-master":"file:///home/dsaucez/master.tgz",
        "ovs":"file:///home/gidilena/distem_img/distem-fs-jessie-ovs.tar.gz",
        }

subnet = "10.0.0.0/24"
login = "login"
password = "password"

# == Helper functions ========================================================
def upload_array_as_file(host, name, lines, clean = False):
    # remove first the file
    if clean:
        cmd = "rm -f %s" %(name)
        print ("o.execute_command(",host, ",", cmd, ")")
    
    for line in lines:
        cmd = 'echo "%s" >> %s' % (line, name)
        print ("o.execute_command(",host, ",", cmd, ")")

def get_ip(name):
    return nodes[name]["ip"]

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

# ============================================================================

slaves = list()     # list of slaves
masters = list()    # list of masters
hosts_file = ["127.0.0.1\tlocalhost localhost.locadomain"] # lines for /etc/hosts


# Let the fun begin
print("o = distem(", login, ",", password, ",", subnet, ")")

# Add all nodes in the topology
for name, infos in nodes.items():
    # Switches
    if infos["type"] == "switch":
        print ("o.add_switch(",name,", image=",images[infos["image"]],")")

    # Hosts
    elif infos["type"] == "host":
        print ("\to.add_node(", name, "image=",images[infos["image"]],")")
        # Specific treatement for Hadoop nodes
        if "hadoop-type" in infos.keys():
            hosts_file.append("%s\t%s" %(get_ip(name), name))
            if infos["hadoop-type"] == "master":
                masters.append(name)
            elif infos["hadoop-type"] == "slave":
                slaves.append(name)

# Add all links in the topology
for link in links:
    print ("o.add_link(", link[0],",", link[1],")")
# Upload
for host in slaves + masters:
    print ("\n#/etc/hosts on", host)
    upload_array_as_file(host, "/etc/hosts", hosts_file, False)

# define cluster files
make_slaves_file(slaves, masters)
make_masters_file(masters)

print ("\n# Format DFS")
cmd = "/root/hadoop/hadoop-2.7.6/bin/hdfs namenode -format"
print ("o.execute_command(",masters[0], ",", cmd, ")")

print ("\n# Start DFS")
cmd = "/root/hadoop/hadoop-2.7.6/sbin/start-dfs.sh"
print ("o.execute_command(",masters[0], ",", cmd, ")")

print ("\n# Start YARN")
cmd = "/root/hadoop/hadoop-2.7.6/sbin/start-yarn.sh"
print ("o.execute_command(",masters[0], ",", cmd, ")")


