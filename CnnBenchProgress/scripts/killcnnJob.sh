#!/usr/bin/env bash
port=$1
ps_pid=$(docker exec -i Tensor-PS bash /root/outins.sh  | grep $port| awk '{print $2}')
w1_pid=$(docker exec -i Tensor-Worker-1 bash /root/outins.sh  | grep $port| awk '{print $2}')
w2_pid=$(docker exec -i Tensor-Worker-2 bash /root/outins.sh  | grep $port| awk '{print $2}')
if [[ $ps_pid ]]
then
    docker exec -i Tensor-PS kill -9 $ps_pid
    echo "Stop Tensor-PS $port"
else
    echo "Currently, Tensor-PS $port don't exist"
fi
if [[ $w1_pid ]]
then
    docker exec -i Tensor-Worker-1 kill -9 $w1_pid
    echo "Stop Tensor-Worker-1 $port"
else
    echo "Currently, Tensor-Worker-1 $port don't exist"
fi
if [[ $w2_pid ]]
then
    docker exec -i Tensor-Worker-2  kill -9 $w2_pid
    echo "Stop Tensor-Worker-2 $port"
else
    echo "Currently, Tensor-Worker-2 $port don't exist"
fi