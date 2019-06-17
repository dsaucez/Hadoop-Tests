# On all nodes:

1. Update .bashrc to point to the correct JDK and Hadoop directories:

   o JDK_DIR=<path to your JDK parent directory>
   
   o HADOOP_DIR=<path to your Hadoop parent directory>


2. Update line 25 of ${HADOOP_DIR}/etc/hadoop/hadoop-env.sh to remplace `JDK_DIR` by the JDK parent directory

3. Update line 6 of ${HADOOP_DIR}/etc/hadoop/core-site.xml to remplace `NODE-MASTER` by the name of the Hadoop master host

4. Update line 17 of ${HADOOP_DIR}/etc/hadoop/yarn-site.xml to remplace `NODE-MASTER` by the name of the Hadoop master host

5. Add the name of each node acting as an Hadoop slave in the ${HADOOP_DIR}/etc/hadoop/slaves file (one name per line)

# On the master node:

1. Add the name of each node acting as an Hadoop slave in the ${HADOOP_DIR}/etc/hadoop/masters file (one name per line)
