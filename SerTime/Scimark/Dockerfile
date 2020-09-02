FROM ubuntu:latest
RUN apt-get update \
    && apt-get install vim openssh-server -y \
    && mkdir /usr/local/jdk1.8.0 \
    && useradd -m tank -g sudo -s /bin/bash -d /home/tank \
    && echo 'tank:tanklab' | chpasswd \
    && echo 'root:root' | chpasswd
COPY ./jdk1.8.0 /usr/local/jdk1.8.0
COPY ./UpdateScimark2.0.jar /root
RUN chmod 777 /usr/local/jdk1.8.0/bin/java
USER tank
WORKDIR /home/tank
# java
ENV JAVA_HOME=/usr/local/jdk1.8.0
ENV JRE_HOME=${JAVA_HOME}/jre
ENV CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
ENV PATH=${JAVA_HOME}/bin:$PATH