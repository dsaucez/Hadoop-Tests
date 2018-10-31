# Running Hadoop 2.7.6 benchmarks

## Preparation

All benchmark results will be place in a DFS _home_ directory that we create as follows:

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hdfs dfs -mkdir -p /user/ubuntu
```

## Benchmarks

### PI

The objective is to estimate the value of PI number.

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hadoop jar  share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.6.jar pi 20 100
```


### Teragen/Terasort/Teravalidate

The objective of this program is to create a large file, then to sort it and verify that the sort has been done correctly.

First we generate a 100 MB file with teragen. With teragen we specify the number of 100 Bytes lines in the file.

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hadoop jar  share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.6.jar teragen 1000000 bench.tera
```

We can then ask the cluster to sort the file with terasort.

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hadoop jar  share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.6.jar terasort bench.tera bench.tera.out
```

Finally we can validate the work with teravalidate
```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hadoop jar  share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.6.jar teravalidate bench.tera.out bench.tera.validate
```


### Wordcount

The objective of wordcount is to count the occurences of each word in files.

First we need a file to count, let's use James Joyce's Ulysse book that we can retrieve from the Gutenberg project:
 
```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ wget http://www.gutenberg.org/files/4300/4300-0.txt
```

We can them copy the book to the DFS in the __wordcount__ directory as follows.

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hadoop dfs -mkdir bench.wordcount
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hadoop dfs -copyFromLocal 4300-0.txt bench.wordcount/Ulysses
```

This being done, we can count occurences of the words in this book as follows:

```bash
ubuntu@node-master:~/hadoop/hadoop-2.7.6$ bin/hadoop jar  share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.6.jar wordcount bench.wordcount/Ulysses bench.wordcount bench.wordcount.out
```

## Notes

This memo took inspirations from
* [Hadoop Performance Evaluation by Benchmarking and Stress Testing with TeraSort and TestDFSIO](https://medium.com/ymedialabs-innovation/hadoop-performance-evaluation-by-benchmarking-and-stress-testing-with-terasort-and-testdfsio-444b22c77db2)
* [Hadoop Tutorial 1 -- Running WordCount](http://www.science.smith.edu/dftwiki/index.php/Hadoop_Tutorial_1_--_Running_WordCount)
