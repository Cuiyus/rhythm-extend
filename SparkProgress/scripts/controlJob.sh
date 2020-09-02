#!/usr/bin/env bash
# 放置于每个spark容器内/root目录下
port=$1
executor_pid=$(lsof -i:$port | grep LISTEN | awk '{print $2}')
if [[ "$executor_pid" != "" ]];then
  echo "Kill CoarseGrainedExecutor：$executor_pid"
  kill -9 $executor_pid
  else
    echo "No CoarseGrainedExecutor"
  fi

