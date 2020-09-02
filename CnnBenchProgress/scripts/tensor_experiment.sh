#!/bin/bash
DATA_DIR=/home/tank-cys/deflation/tensorflow/data
PYTHON=/
if [ ! -d ${DATA_DIR} ];
then 
	mkdir -p ${DATA_DIR}
	echo "DATA_DIR:/home/tank-cys/deflation/tensorflow/data"
else
	echo "${DATA_DIR}"
fi
echo "Set env->Training Device: CPU"
docker exec -e CUDA_VISIBLE_DEVICES=-1 Tensor-PS bash
docker exec -e CUDA_VISIBLE_DEVICES=-1 Tensor-Worker-1 bash
docker exec -e CUDA_VISIBLE_DEVICES=-1 Tensor-Worker-2 bash

stat=${1:-start}
shift
model=${1:-resnet20} 
batch_size=${2:-16}
num_epochs=${3:-20}
sync=${4:-False}
if [[ $stat == 'start' ]]
then
    ps_pid=$(docker exec -i Tensor-PS ps aux|grep python|grep -v grep|awk '{print $2}')
    if [[ $ps_pid ]]
    then
        echo "PS has exited"
    else
        echo "Start PS With sync : ${sync}"
        docker exec -i Tensor-PS python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=$batch_size --model=$model --print_training_accuracy=True --num_epochs=$num_epochs --job_name=ps --ps_hosts=172.17.0.11:8888 --worker_hosts=172.17.0.12:8888,172.17.0.13:8888 --task_index=0 --cross_replica_sync=$sync --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> /dev/null 2>&1 &
    fi 
    echo "Start Work-1"
    read -p "Please Enter Worker-1 Data Name:" DATA_NAME_1
    if [ -d ${DATA_DIR}/$DATA_NAME_1 ]
    then 
	read -p "Please Enter Worker-1 Data Name again:" DATA_NAME_1
    fi
    echo "Start Work-2"
    read -p "Please Enter Worker-2 Data Name:" DATA_NAME_2
    if [ -d ${DATA_DIR}/$DATA_NAME_2 ]
    then
        read -p "Please Enter Worker-2 Data Name again:" DATA_NAME_2
    fi
    docker exec -i Tensor-Worker-1 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=$batch_size --model=$model --print_training_accuracy=True --num_epochs=$num_epochs --job_name=worker --ps_hosts=172.17.0.11:8888 --worker_hosts=172.17.0.12:8888,172.17.0.13:8888 --task_index=0 --cross_replica_sync=$sync --num_intra_threads=10 --num_inter_threads=10 --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> $DATA_DIR/${DATA_NAME_1} &
    docker exec -i Tensor-Worker-2 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=$batch_size --model=$model --print_training_accuracy=True --num_epochs=$num_epochs --job_name=worker --ps_hosts=172.17.0.11:8888 --worker_hosts=172.17.0.12:8888,172.17.0.13:8888 --task_index=1 --cross_replica_sync=$sync --num_intra_threads=10 --num_inter_threads=10 --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> $DATA_DIR/${DATA_NAME_2} & 
    # docker exec -i Tensor-Worker-3 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=$batch_size --model=$model --print_training_accuracy=True --num_epochs=$num_epochs --job_name=worker --ps_hosts=172.17.0.11:8888 --worker_hosts=172.17.0.12:8888,172.17.0.13:8888 --task_index=2 --cross_replica_sync=$sync --num_intra_threads=10 --num_inter_threads=10 --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> $DATA_DIR/${DATA_NAME_2} &
    # docker exec -i Tensor-Worker-4 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=$batch_size --model=$model --print_training_accuracy=True --num_epochs=$num_epochs --job_name=worker --ps_hosts=172.17.0.11:8888 --worker_hosts=172.17.0.12:8888,172.17.0.13:8888,172.17.0.14:8888,172.17.0.15:8888 --task_index=3 --cross_replica_sync=$sync --num_intra_threads=10 --num_inter_threads=10 --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> $DATA_DIR/${DATA_NAME_2} &
elif [[ $stat == 'stop' ]]
then 
    ps_pid=$(docker exec -i Tensor-PS ps aux|grep python|grep -v grep|awk '{print $2}')
    w1_pid=$(docker exec -i Tensor-Worker-1 ps aux|grep python|grep -v grep|awk '{print $2}')
    w2_pid=$(docker exec -i Tensor-Worker-2 ps aux|grep python|grep -v grep|awk '{print $2}')
    # w3_pid=$(docker exec -i Tensor-Worker-3 ps aux|grep python|grep -v grep|awk '{print $2}')
    # w4_pid=$(docker exec -i Tensor-Worker-4 ps aux|grep python|grep -v grep|awk '{print $2}')
    if [[ $ps_pid ]]
    then
        echo "PSID:${ps_pid}"
        docker exec -i Tensor-PS kill -9 $ps_pid
        echo "Stop Tensor-PS"
    else
        echo "Currently, Tensor-PS don't exist"
    fi
    if [[ $w1_pid ]]
    then
        docker exec -i Tensor-Worker-1 kill -9 $w1_pid
        echo "Stop Tensor-Worker-1"
    else
        echo "Currently, Tensor-Worker-1 don't exist"
    fi
    if [[ $w2_pid ]]
    then
        docker exec -i Tensor-Worker-2 kill -9 $w2_pid
        echo "Stop Tensor-Worker-2"
    else
        echo "Currently, Tensor-Worker-2 don't exist"
    fi
    # if [[ $w3_pid ]]
    # then
    #     docker exec -i Tensor-Worker-3 kill -9 $w3_pid
    #     echo "Stop Tensor-Worker-3"
    # else
    #     echo "Currently, Tensor-Worker-3 don't exist"
    # fi
    # if [[ $w4_pid ]]
    # then
    #     docker exec -i Tensor-Worker-4 kill -9 $w4_pid
    #     echo "Stop Tensor-Worker-4"
    # else
    #     echo "Currently, Tensor-Worker-4 don't exist"
    # fi
fi
