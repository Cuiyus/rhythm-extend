#!/usr/bin/env bash
# 运行scimark
# 放置于容器中
java -jar /root/UpdateScimark2.0.jar 2 >> /dev/null &
starttime=$(date +%s%3N)
echo  "$! $starttime" >> /share/sci.log
