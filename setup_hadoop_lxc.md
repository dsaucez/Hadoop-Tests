# Setup a $n$-nodes Hadoop 2.7.6 Cluster in LXC

## Topology
TBD

## Prepare a base Ubuntu Xenial container

### Create the container
```bash
dsaucez@ubuntu:~$ lxc-create -t download -n hadoop-cluster -- --dist ubuntu --release xenial --arch amd64
Using image from local cache
Unpacking the rootfs

---
You just created an Ubuntu xenial amd64 (20181004_07:42) container.

To enable SSH, run: apt install openssh-server
No default root or user password are set by LXC.
```

### Start the container
```bash
dsaucez@ubuntu:~$ lxc-start -n hadoop-cluster
```

### Install required SSH server and RSYNC services

```bash
dsaucez@ubuntu:~$ lxc-attach -n hadoop-cluster
root@hadoop-cluster:/# apt install openssh-server
[...]
root@hadoop-cluster:/# apt install rsync
[...]
```

### Set password for ssh connection

Ubuntu Xenial comes by default with a sudoer user called *ubuntu* with no assigned password. For SSH connection, we allocate this user a password.

``` bash
root@hadoop-cluster:/# passwd ubuntu
Enter new UNIX password: 
Retype new UNIX password: 
passwd: password updated successfully
```

### Install Oracle Java 8

To install Oracle Java you will have to accept the _"Oracle Binary Code License Agreement for the Java SE Platform Products and JavaFX"_. The license is available in http://java.com/license. The installation process will ask you to accept the terms of that license.

Oracle Java is not available directly, 

```bash
root@hadoop-cluster:/# apt install software-properties-common
[...]
root@hadoop-cluster:/# sudo add-apt-repository ppa:webupd8team/java
[...]
root@hadoop-cluster:/# apt-get update
[...]
root@hadoop-cluster:/# sudo apt-get install oracle-java8-installer
[...]
root@hadoop-cluster:/# java -version
java version "1.8.0_191"
Java(TM) SE Runtime Environment (build 1.8.0_191-b12)
Java HotSpot(TM) 64-Bit Server VM (build 25.191-b12, mixed mode)
```

At this stage all system software are properly installed, we can focus on Hadoop.

```bash
root@hadoop-cluster:/# exit
exit
```

## Prepare base Hadoop

### Install Hadoop files
In this part we will download Hadoop software and configure elements that are common with all nodes in the cluster

First identify the IP address of the container.

```bash
dsaucez@ubuntu:~$ lxc-info -n hadoop-cluster -i
IP:             10.0.3.147
```

Then can connect with the user *ubuntu* directly to the container in SSH.

```bash
dsaucez@ubuntu:~$ ssh ubuntu@10.0.3.147
The authenticity of host '10.0.3.147 (10.0.3.147)' can't be established.
ECDSA key fingerprint is SHA256:qHBu4va22TuR5blDTJ/Dn5lX9lJ4G/hA/lDknEcDz/w.
Are you sure you want to continue connecting (yes/no)? yes
[...]
ubuntu@hadoop-cluster:~$ 
```

Create a directory where to put Hadoop files, download Hadoop 2.7.6 archive, and extract it in the directory.

```bash
ubuntu@hadoop-cluster:~$ mkdir hadoop
ubuntu@hadoop-cluster:~$ cd hadoop/
ubuntu@hadoop-cluster:~/hadoop$ wget http://mirrors.standaloneinstaller.com/apache/hadoop/common/hadoop-2.7.6/hadoop-2.7.6.tar.gz
[...]
ubuntu@hadoop-cluster:~/hadoop$ tar -xzf hadoop-2.7.6.tar.gz 
ubuntu@hadoop-cluster:~/hadoop$ rm hadoop-2.7.6.tar.gz
ubuntu@hadoop-cluster:~/hadoop$ cd hadoop-2.7.6
```

Modify __etc/hadoop/hadoop-env.sh__ to specify the Java implementation to use. The line 25 becomes:
```bash
export JAVA_HOME=/usr/lib/jvm/java-8-oracle
```

Where _export JAVA_HOME=/usr/lib/jvm/java-8-oracle_ corresponds is obtained by

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ echo $JAVA_HOME
/usr/lib/jvm/java-8-oracle
```

**Important notice**

Please keep in mind that Hadoop 2.7.6 files come with the following license that you must respect.

>  Licensed under the Apache License, Version 2.0 (the "License");
>  you may not use this file except in compliance with the License.
>  You may obtain a copy of the License at
>
>    http://www.apache.org/licenses/LICENSE-2.0
>
>  Unless required by applicable law or agreed to in writing, software
>  distributed under the License is distributed on an "AS IS" BASIS,
>  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
>  See the License for the specific language governing permissions and
>  limitations under the License. See accompanying LICENSE file.

We can check that all went well

```bash
ubuntu@hadoop-cluster:~/hadoop/hadoop-2.7.6$ bin/hadoop version
Hadoop 2.7.6
Subversion https://shv@git-wip-us.apache.org/repos/asf/hadoop.git -r 085099c66cf28be31604560c376fa282e69282b8
Compiled by kshvachk on 2018-04-18T01:33Z
Compiled with protoc 2.5.0
From source with checksum 71e2695531cb3360ab74598755d036
This command was run using /home/ubuntu/hadoop/hadoop-2.7.6/share/hadoop/common/hadoop-common-2.7.6.jar
```

If you have an error, check all the previous steps.

### Prepare common configuration files

Edit __etc/hadoop/core-site.xml__ to be:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>fs.default.name</name>
    <value>hdfs://node-master:9000</value>
  </property>
</configuration>
```

Edit __etc/hadoop/mapred-site.xml__ to be:

```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
</configuration>
```

Edit __etc/hadoop/yarn-site.xml__ to be:

```xml
<?xml version="1.0"?>
<configuration>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>
  <property>
    <name>yarn.nodemanager.auxservices.mapreduce.shuffle.class</name>
    <value>org.apache.hadoop.mapred.ShuffleHandler</value>
  </property>
  <property>
    <name>yarn.acl.enable</name>
    <value>0</value>
  </property>
  <property>
    <name>yarn.resourcemanager.hostname</name>
    <value>node-master</value>
  </property>
</configuration>
```

The base image is created, we will now use it as a base for setting up the master and the slaves in the cluster. For that, let's first stop the base image we worked on.

```bash
ubuntu@hadoop-cluster:~/hadoop/hadoop-2.7.6$ exit
logout
Connection to 10.0.3.147 closed.
dsaucez@ubuntu:~$ lxc-stop -n hadoop-cluster
```

## Prepare Master image
Let's copy the base image to run the __node-master_ node.

```bash
dsaucez@ubuntu:~$ lxc-copy -n hadoop-cluster -N node-master
dsaucez@ubuntu:~$ lxc-start -n node-master
```

We can connect to the __node-master__ node and make its specific configuration.

```bash
dsaucez@ubuntu:~$ lxc-info -n node-master -i
IP:             10.0.3.147
dsaucez@ubuntu:~$ ssh ubuntu@10.0.3.147
ubuntu@10.0.3.147's password: 
[...]
```

We will use key-based authentication for the master node to seamlessly connect to all the nodes in the cluster. For that we create a passphrase'less SSH key.

```bash
ubuntu@node-master:~$ ssh-keygen -P "" -f /home/ubuntu/.ssh/id_rsa
[...]
```

We add the public key to the local machine (i.e., _localhost_) for automated SSH connection, we will add it to the other machines in the cluster later on.

```bash
ubuntu@node-master:~$ ssh-copy-id -i $HOME/.ssh/id_rsa.pub localhost
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/home/ubuntu/.ssh/id_rsa.pub"
The authenticity of host 'localhost (::1)' can't be established.
ECDSA key fingerprint is SHA256:qHBu4va22TuR5blDTJ/Dn5lX9lJ4G/hA/lDknEcDz/w.
Are you sure you want to continue connecting (yes/no)? yes
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed -- if you are prompted now it is to install the new keys
ubuntu@localhost's password: 

Number of key(s) added: 1
[...]
```

If everything went well, you should be able to connect without entering any password to _localhost_.

```bash
ubuntu@node-master:~$ ssh localhost
Welcome to Ubuntu 16.04.5 LTS (GNU/Linux 4.4.0-131-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage
Last login: Fri Oct 19 18:08:46 2018 from 10.0.3.1
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@node-master:~$ exit

logout
Connection to localhost closed.
```

To avoid host verification with SSH, edit the __.ssh/config__ file to have

```bash
Host *
    StrictHostKeyChecking no
```

Make sure only root has access to it:

```bash
ubuntu@node-master:~$ chmod 400 /root/.ssh/config
```

### Configure the master'specific Hadoop files

Go to the Hadoop distribution directory.

```bash
ubuntu@node-master:~$ cd hadoop/hadoop-2.7.6/
ubuntu@node-master:~/hadoop/hadoop-2.7.6$
```

Edit __etc/hadoop/hdfs-site.xml__ to be:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>2</value>
  </property>
  <property>
    <name>dfs.permissions</name>
    <value>false</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>/home/ubuntu/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>/home/ubuntu/datanode</value>
  </property>
</configuration>
```

The master image is properly configured, we can disconnect from it.

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ exit
logout
Connection to 10.0.3.147 closed.
dsaucez@ubuntu:~$
```

## Prepare slave image

Let's copy the base image to prepare a slave node.

```bash
dsaucez@ubuntu:~$ lxc-copy -n hadoop-cluster -N node-slave
dsaucez@ubuntu:~$ lxc-start -n node-slave
```

We can connect to the __node-slave__ node and make its specific configuration.

```bash
dsaucez@ubuntu:~$ lxc-info -n node-slave -i
IP:             10.0.3.173
dsaucez@ubuntu:~$ ssh ubuntu@10.0.3.173
The authenticity of host '10.0.3.173 (10.0.3.173)' can't be established.
ECDSA key fingerprint is SHA256:qHBu4va22TuR5blDTJ/Dn5lX9lJ4G/hA/lDknEcDz/w.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '10.0.3.173' (ECDSA) to the list of known hosts.
ubuntu@10.0.3.173's password: 
[...]
```

We can install the node-master key in the slave to allow seamless connection from the master to the slave. For that we connect in SSH from the slave to __node-master__ install the key as previously.

```bash
ubuntu@node-slave:~$ ssh 10.0.3.147
The authenticity of host '10.0.3.147 (10.0.3.147)' can't be established.
ECDSA key fingerprint is SHA256:qHBu4va22TuR5blDTJ/Dn5lX9lJ4G/hA/lDknEcDz/w.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '10.0.3.147' (ECDSA) to the list of known hosts.
ubuntu@10.0.3.147's password: 
[...]
ubuntu@node-master:~$ ssh-copy-id -i $HOME/.ssh/id_rsa.pub 10.0.3.173
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/home/ubuntu/.ssh/id_rsa.pub"
The authenticity of host '10.0.3.173 (10.0.3.173)' can't be established.
ECDSA key fingerprint is SHA256:qHBu4va22TuR5blDTJ/Dn5lX9lJ4G/hA/lDknEcDz/w.
Are you sure you want to continue connecting (yes/no)? yes
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 1 key(s) remain to be installed -- if you are prompted now it is to install the new keys
ubuntu@10.0.3.173's password: 

Number of key(s) added: 1
[...]
ubuntu@node-master:~$ ssh 10.0.3.173
Welcome to Ubuntu 16.04.5 LTS (GNU/Linux 4.4.0-131-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage
Last login: Fri Oct 19 18:32:06 2018 from 10.0.3.1
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

ubuntu@node-slave:~$ 
```

Don't forget to disconnect from your test and from __node-master__ to get back to the slave node.
```bash
ubuntu@node-slave:~$ exit
logout
Connection to 10.0.3.173 closed.
ubuntu@node-master:~$ exit
logout
Connection to 10.0.3.147 closed.
ubuntu@node-slave:~$ 
```

### Configure the slave'specific Hadoop files

Go to the Hadoop distribution directory.

```bash
ubuntu@node-slave:~$ cd hadoop/hadoop-2.7.6/
ubuntu@node-slave:~/hadoop/hadoop-2.7.6$
```

Edit __etc/hadoop/hdfs-site.xml__ to be:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>2</value>
  </property>
  <property>
    <name>dfs.permissions</name>
    <value>false</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>/home/ubuntu/datanode</value>
  </property>
</configuration>
```

The slave image is properly configured, we can disconnect from it and stop it.

```bash
ubuntu@node-slave:~/hadoop/hadoop-2.7.6$ exit
logout
Connection to 10.0.3.173 closed.
dsaucez@ubuntu:~$ lxc-stop -n node-slave
```

## Starting the cluster

In this example, all the slave nodes have a name starting with _slave-_.

The master node, called __node-master__ already runs. We have to instantiate $n$ slave nodes, namely __slave-1__, ..., __slave-$n$__. They are copies of the __node-slave__ slave base image that we just created and stopped.

To automatically create them we can run the following script (for $n=3$) then check if they have been correctly instantiated.

```bash
nb_slaves=3
for (( i=1; i<=$nb_slaves; i++));
do
  lxc-copy -n node-slave -N slave-$i
  lxc-start -n slave-$i
done
```

like this:

```bash
dsaucez@ubuntu:~$ for (( i=1; i<=$nb_slaves; i++));
> do
>   lxc-copy -n node-slave -N slave-$i
>   lxc-start -n slave-$i
> done
dsaucez@ubuntu:~$ lxc-ls -f
NAME            STATE   AUTOSTART GROUPS IPV4       IPV6 
hadoop-cluster  STOPPED 0         -      -          -    
node-master     RUNNING 0         -      10.0.3.147 -    
node-slave      STOPPED 0         -      -          -    
slave-1         RUNNING 0         -      10.0.3.173 -    
slave-2         RUNNING 0         -      10.0.3.121 -    
slave-3         RUNNING 0         -      10.0.3.212 -    
```

The slave nodes and the master node are now working, we have to configure them to be able to resolve each other names. As we did not install a DNS server, we will use the _/etc/hosts_ file. Also we have to make sure the the hostname (e.g., _slave-1_) points to a global address and not the loopback interface.

```bash
nb_slaves=3
nodes[0]="node-master"
for (( i=1; i<=$nb_slaves; i++));
do
  nodes[$i]="slave-$i"
done
for node in ${nodes[*]};
do
  echo "127.0.0.1 localhost" | lxc-attach -n $node -- /bin/sh -c "/bin/cat > /etc/hosts"
  lxc-ls -f | grep -E "(slave-|node-master).\ *RUNNING" | awk '{print $5,$1}' | lxc-attach -n $node -- /bin/sh -c "/bin/cat >> /etc/hosts"
done
```

like this:

```bash
dsaucez@ubuntu:~$ nb_slaves=3
dsaucez@ubuntu:~$ nodes[0]="node-master"
dsaucez@ubuntu:~$ for (( i=1; i<=$nb_slaves; i++));
> do
>   nodes[$i]="slave-$i"
> done
dsaucez@ubuntu:~$ for node in ${nodes[*]};
> do
>   lxc-ls -f | grep -E "(slave-|node-master).\ *RUNNING" | awk '{print $5,$1}' | lxc-attach -n $node -- /bin/sh -c "/bin/cat >> /etc/hosts"
> done
```

The last step is to indicate on each node in the cluster the name of the master and the name of the slaves. For that the __etc/hadoop/master__ and __etc/hadoop/slaves__ must be updated to contain the list of the nodes, each node taking one line.

We can run the following script to build these 2 files:

```bash
nb_slaves=3
nodes[0]="node-master"
for (( i=1; i<=$nb_slaves; i++));
do
  nodes[$i]="slave-$i"
  echo "slave-$i" >> $$
done

echo ""
for node in ${nodes[*]};
do
	cat $$ | lxc-attach -n $node -- /bin/sh -c "/bin/cat > /home/ubuntu/hadoop/hadoop-2.7.6/etc/hadoop/slaves"
	echo ${nodes[0]} | lxc-attach -n $node -- /bin/sh -c "/bin/cat > /home/ubuntu/hadoop/hadoop-2.7.6/etc/hadoop/masters"
done
rm $$
```

like this:

```bash
dsaucez@ubuntu:~$ nb_slaves=3
dsaucez@ubuntu:~$ nodes[0]="node-master"
dsaucez@ubuntu:~$ for (( i=1; i<=$nb_slaves; i++));
> do
>   nodes[$i]="slave-$i"
>   echo "slave-$i" >> $$
> done
dsaucez@ubuntu:~$ 
dsaucez@ubuntu:~$ echo ""

dsaucez@ubuntu:~$ for node in ${nodes[*]};
> do
> cat $$ | lxc-attach -n $node -- /bin/sh -c "/bin/cat > /home/ubuntu/hadoop/hadoop-2.7.6/etc/hadoop/slaves"
> echo ${nodes[0]} | lxc-attach -n $node -- /bin/sh -c "/bin/cat > /home/ubuntu/hadoop/hadoop-2.7.6/etc/hadoop/masters"
> done
```

At this stage the cluster is setup, we can run our first experiment.

## Testing the installation

We connect to the master node in SSH and go to the Hadoop distribution directory.

```bash
dsaucez@ubuntu:~$ ssh ubuntu@node-master
ubuntu@node-master's password: 
[...]
ubuntu@node-master:~$ cd hadoop/hadoop-2.7.6/
ubuntu@node-master:~/hadoop/hadoop-2.7.6$
```

### Deploy the distributed file system

1. Format the distributed file system

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hdfs namenode -format
[...]
```

2. Start DFS

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ sbin/start-dfs.sh 
[...]
```

If all went well, the service is running, this can be checked with the _jps_ command.

On the master node, you should see _NameNode_ and _SecondaryNameNode_. Something similar to:
```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ jps
573 SecondaryNameNode
366 NameNode
1167 Jps
```

On the slave nodes, you should see _DataNode_. Somethind similar to:
```bash
ubuntu@slave-1:~$ jps
700 Jps
253 DataNode
```

You can see various information about the file system with the __bin/hdfs__ command. For example, you should observe something similar to the following:

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hdfs dfsadmin -printTopology
Rack: /default-rack
   10.0.3.121:50010 (slave-2)
   10.0.3.173:50010 (slave-1)
   10.0.3.212:50010 (slave-3)
```

### Deploy YARN

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ sbin/start-yarn.sh 
[...]
```

The new service is started and it can be checked with the _jps_ command.

On the master node, you should see now the _ResourceManager_. Something similar to:
```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ jps
1721 ResourceManager
1994 Jps
573 SecondaryNameNode
366 NameNode
```

On the slave nodes, you should see now the _NodeManager_. Something similar to:
```bash
ubuntu@slave-1:~$ jps
932 Jps
253 DataNode
781 NodeManager
```

You can see various information related to YARN with the _bin/yarn_ command. For example, you should observe something similar to the following:
```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/yarn node -list
18/10/19 21:16:52 INFO client.RMProxy: Connecting to ResourceManager at node-master/10.0.3.147:8032
Total Nodes:4
         Node-Id	     Node-State	Node-Http-Address	Number-of-Running-Containers
   slave-2:39014	        RUNNING	     slave-2:8042	                           0
node-master:38750	        RUNNING	 node-master:8042	                           0
   slave-3:37299	        RUNNING	     slave-3:8042	                           0
   slave-1:33220	        RUNNING	     slave-1:8042	                           0
```

## Notes

This memo took inspirations from

* [Multi Node Cluster in Hadoop 2.x](https://www.edureka.co/blog/setting-up-a-multi-node-cluster-in-hadoop-2.X)
* [Apache Hadoop 2.9.1 – Hadoop: Setting up a Single Node Cluster.](https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-common/SingleCluster.html)
