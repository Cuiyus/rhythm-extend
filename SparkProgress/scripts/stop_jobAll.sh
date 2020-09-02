#!/usr/bin/env bash
applist=$(docker exec -i Spark-1 yarn application -list | grep http | grep application | awk '{print $1}' )
for app in $applist; do
  echo "Delete Job $app"
  docker exec -i Spark-1 yarn application -kill $app
  done

