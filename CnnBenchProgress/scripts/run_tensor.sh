#!/bin/bash
ps=172.28.0.5
worker1=172.28.0.6
worker2=172.28.0.7
port=22222

ps_pid=$(docker exec -i Tensor-PS ps aux|grep tf_cnn_benchmarks|grep -v grep|awk '{print $2}')

if [[ "$ps_pid" && "$ps_pid" != "1" ]]
then
    echo "PS has exited"
else
    echo "Start PS"
    docker exec -e CUDA_VISIBLE_DEVICES=-1 -i Tensor-PS python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=16 --model=resnet20 --print_training_accuracy=True --num_batches=2000 --job_name=ps --ps_hosts=$ps:$port --worker_hosts=$worker1:$port,$worker2:$port --task_index=0  --cross_replica_sync=False --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> /dev/null 2>&1 &
fi

echo "Start Work-1"
docker exec -e CUDA_VISIBLE_DEVICES=-1 -i Tensor-Worker-1 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=16 --model=resnet20 --print_training_accuracy=True --num_batches=2000 --job_name=worker --ps_hosts=$ps:$port --worker_hosts=$worker1:$port,$worker2:$port --task_index=0 --cross_replica_sync=False --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> /dev/null 2>&1 &
echo "Start Work-2"
docker exec -e CUDA_VISIBLE_DEVICES=-1 -i Tensor-Worker-2 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=16 --model=resnet20 --print_training_accuracy=True --num_batches=2000 --job_name=worker --ps_hosts=$ps:$port --worker_hosts=$worker1:$port,$worker2:$port --task_index=1 --cross_replica_sync=False --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> /dev/null 2>&1 &

echo "Running"
docker exec -i Tensor-Worker-1 bash outloss.sh >> ./test.txt