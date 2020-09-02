#!/usr/bin/env bash
# 该脚本需要放置在容器内
instanceID=$1
while [[ "1" == "1" ]]
do
if [ ! -f "/root/${instanceID}.txt" ];then
  continue
else
  tail -n 1 -f /root/${instanceID}.txt
  break
fi
done