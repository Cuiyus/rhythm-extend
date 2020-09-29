#!/bin/bash
ps -ef | grep memBw|cut -c 9-15|xargs kill -9
ps -ef | grep l3|cut -c 9-15|xargs kill -9
ps -ef | grep cpu|cut -c 9-15|xargs kill -9
ps -ef | grep python|cut -c 9-15|xargs kill -9
ps -ef | grep single|cut -c 9-15|xargs kill -9
applist=$(docker exec -i Spark-1 yarn application -list | grep http | grep application | awk '{print $1}' )
for app in $applist; do
  echo "Delete Job $app"
  docker exec -i Spark-1 yarn application -kill $app
  done
