FROM ubuntu:latest
RUN apt-get update \
    && apt install -y jq vim \
    && mkdir /home/tank
COPY ./beleader /home/tank
ENV TZ Asia/Shanghai
VOLUME /share
WORKDIR /home/tank