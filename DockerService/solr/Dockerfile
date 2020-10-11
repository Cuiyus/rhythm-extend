FROM cuiys/java:v1
COPY ./solr-6.6.0.tgz /home/tank
COPY ./zookeeper-3.4.10.tar.gz /home/tank
COPY ./runssh.sh /home/tank
USER root
RUN mkdir /run/sshd \
    && tar -zxvf zookeeper-3.4.10.tar.gz -C /usr/local/ \
    && tar -zxvf solr-6.6.0.tgz -C /usr/local/ \
    && mkdir -p /home/tank/zookeeper/data \
    && mkdir -p /home/tank/zookeeper/log \
    && mkdir -p /usr/local/solrCloud/solr_cloud_home \
    && cp -r /usr/local/solr-6.6.0/server/solr/* /usr/local/solrCloud/solr_cloud_home/ \
    && mkdir -p /usr/local/solr_cloud_collection/cloud_core \
    && cp -r /usr/local/solr-6.6.0/example/example-DIH/solr/solr/* /usr/local/solr_cloud_collection/cloud_core/
#java1
USER tank
ENV JAVA_HOME=/usr/local/jdk1.8.0
ENV JRE_HOME=${JAVA_HOME}/jre
ENV CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
ENV PATH=${JAVA_HOME}/bin:$PATH
WORKDIR /home/tank
