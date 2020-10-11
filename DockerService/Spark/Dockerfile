FROM ubuntu:latest
RUN apt-get update \
    && apt-get install vim openssh-server lsof -y \
#    && mkdir /usr/local/jdk1.8.0 \
    && mkdir /root/hadoop \
    && mkdir /root/scala \
    && mkdir /root/spark \
    && mkdir /run/sshd \
    && mkdir /usr/share/zoneinfo
#COPY ./jdk1.8.0 /usr/local
COPY ./zoneinfo /usr/share/zoneinfo
COPY ./hadoop /root/hadoop 
COPY ./scala /root/scala
COPY ./spark /root/spark
COPY ./sshrun.sh /root
COPY ./jdk-8u201-linux-x64.tar.gz /root
COPY ./controlJob.sh /root

RUN tar zxvf /root/jdk-8u201-linux-x64.tar.gz -C /usr/local/ \
    && mv /usr/local/jdk1.8.0_201 /usr/local/jdk1.8.0 \
    && chmod -R 777 /root/hadoop \
    && chmod -R 777 /root/spark \
    && chmod -R 777 /root/scala \
    && echo "PermitRootLogin yes" >>  /etc/ssh/sshd_config \
    && sed -ri 's/session required pam_loginuid.so/#session required pam_loginuid.so/g' /etc/pam.d/sshd \
    && chmod 755 /root/sshrun.sh \
    && echo "root:root" |chpasswd \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo 'Asia/Shanghai' >/etc/timezone 
#    && echo -e "172.27.0.5    master \n172.27.0.6    slave1 \n172.27.0.7    slave2" >> /etc/hosts
#    && bash /root/sshrun.sh
WORKDIR /root
VOLUME /share
# Hadoop
ENV HADOOP_HOME=/root/hadoop/hadoop2.7.7
ENV HADOOP_CONFIG_HOME=$HADOOP_HOME/etc/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin
ENV PATH=$PATH:$HADOOP_HOME/sbin
# Spark 
ENV SPARK_HOME=/root/spark/spark2.4.4
ENV PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH
# Scala
ENV SCALA_HOME=/root/scala/scala2.12.7
ENV PATH=$PATH:$SCALA_HOME/bin
# java 
ENV JAVA_HOME=/usr/local/jdk1.8.0
ENV JRE_HOME=${JAVA_HOME}/jre
ENV CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
ENV PATH=${JAVA_HOME}/bin:$PATH
EXPOSE 18080
EXPOSE 50070
EXPOSE 8080
EXPOSE 8088           
EXPOSE 4040
CMD ["/usr/sbin/sshd","-D"]
