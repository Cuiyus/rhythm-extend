#!/bin/bash
ps -ef | grep memBw|cut -c 9-15|xargs kill -9
ps -ef | grep l3|cut -c 9-15|xargs kill -9
ps -ef | grep cpu|cut -c 9-15|xargs kill -9
ps -ef | grep python|cut -c 9-15|xargs kill -9
ps -ef | grep single|cut -c 9-15|xargs kill -9
ps -ef | grep java|cut -c 9-15|xargs kill -9
ps -ef | grep outloss|cut -c 9-15|xargs kill -9
applist=$(yarn application -list | grep http | grep application | awk '{print $1}' )
for app in $applist; do
  echo "Delete Job $app"
  yarn application -kill $app
  done
