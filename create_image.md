# Create a Distem rootfs file with Hadoop 2.7.6


* Take a base image archive, for example _/home/amerlin/public/distem/distem-fs-jessie-ovs.tar.gz_ and copy it in your directory, let's call it base.tar.gz
```bash
dsaucez@fnancy:~$ mkdir hadoop
dsaucez@fnancy:~$ cd hadoop/
dsaucez@fnancy:~/hadoop$ cp /home/amerlin/public/distem/distem-fs-jessie-ovs.tar.gz base.tar.gz
```

* Decompress the archive (but keep it as an archive)
```bash
dsaucez@fnancy:~/hadoop$ gunzip base.tar.gz
```

* delete from the image all the files you don't need, or that you want to replace. In our case as we modify /root/.profile, let's remove it:
```bash
dsaucez@fnancy:~/hadoop$ tar -f base.tar --delete ./root/.profile
```

* Create a _root_ directory, it will correspond to the _/root_ in our image.

```bash
dsaucez@fnancy:~/hadoop$ mkdir root
```

* Download Java and Hadoop 2.7.6 as shown in `Setup a $n$-nodes Hadoop 2.7.6 Cluster in LXC` in this directory. You should have something like:

```bash
dsaucez@fnancy:~/hadoop$ ls root/
hadoop-2.7.6  jdk-11.0.1
```

* Configure Java and Hadoop 2.7.6 as shown in `Setup a $n$-nodes Hadoop 2.7.6 Cluster in LXC` just by editing the files in your _root/<dir>_ directory. Where _<dir>_ corresponds to the Hadoop or Java directory.

* Create a _.profile_ file that will contain the correct path to Java and Hadoop in this directory

```bash
dsaucez@fnancy:~/hadoop$ touch root/.profile
````

and edit it to have the following content:

```bash
# ~/.profile: executed by Bourne-compatible login shells.

if [ "$BASH" ]; then
  if [ -f ~/.bashrc ]; then
    . ~/.bashrc
  fi
fi

mesg n

PATH=/root/jdk-11.0.1/bin:/root/hadoop-2.7.6/bin/:/root/hadoop-2.7.6/sbin/:${PATH}
JAVA_HOME=/root/jdk-11.0.1:${JAVA_HOME}
```

* Add Hadoop, Java and the r files to the image, for example our _/root_ directory:
```bash
tar -f base.tar --owner=0 --group=0 --append ./root/hadoop-2.7.6 ./root/jdk-11.0.1 ./root/.profile
```

* Compress the image:

```bash
dsaucez@fnancy:~/hadoop$ gzip base.tar 
```

You have now a _base.tar.gz_ that can be used as *rootfs* with Distem.
