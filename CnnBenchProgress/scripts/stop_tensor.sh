#!/bin/bash
ps_pid=$(docker exec -i Tensor-PS ps aux|grep tf_cnn_benchmarks|grep -v grep|awk '{print $2}')
w1_pid=$(docker exec -i Tensor-Worker-1  ps aux|grep tf_cnn_benchmarks|grep -v grep|awk '{print $2}')
w2_pid=$(docker exec -i Tensor-Worker-2 ps aux|grep tf_cnn_benchmarks|grep -v grep|awk '{print $2}')
if [[ $ps_pid ]]
then
    outloss_id=$(docker exec -i Tensor-PS ps aux|grep tail |grep -v grep|awk '{print $2}')
    docker exec -i Tensor-PS kill -9 $ps_pid $outloss_id
    echo "Stop Tensor-PS"
else
    echo "Currently, Tensor-PS don't exist"
fi
if [[ $w1_pid ]]
then
    outloss_id=$(docker exec -i Tensor-Worker-1 ps aux|grep tail |grep -v grep|awk '{print $2}')
    docker exec -i Tensor-Worker-1 kill -9 $w1_pid $outloss_id
    echo "Stop Tensor-Worker-1"
else
    echo "Currently, Tensor-Worker-1 don't exist"
fi
if [[ $w2_pid ]]
then
    outloss_id=$(docker exec -i Tensor-Worker-2 ps aux|grep tail |grep -v grep|awk '{print $2}')
    docker exec -i Tensor-Worker-2  kill -9 $w2_pid $outloss_id
    echo "Stop Tensor-Worker-2"
else
    echo "Currently, Tensor-Worker-2 don't exist"
fi
