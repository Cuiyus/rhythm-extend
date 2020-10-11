FROM mytensorflow:v1
RUN mkdir /root/benchmarks-master \
    && mkdir /root/cifar-10-batches-py \
    && mkdir /run/sshd \
    && apt-get update \
    && apt-get install vim net-tools openssh-server lsof pssh -y\
    && echo "root:root" |chpasswd \
    && echo "PermitRootLogin yes" >>  /etc/ssh/sshd_config

COPY ./benchmarks-master /root/benchmarks-master
COPY ./cifar-10-batches-py /root/cifar-10-batches-py
COPY ./outloss.sh /root
COPY ./outins.sh /root
WORKDIR /root
VOLUME /share
CMD ["/usr/sbin/sshd","-D"]
