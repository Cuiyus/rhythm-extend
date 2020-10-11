#!/bin/bash
ps=172.28.0.5
worker1=172.28.0.6
worker2=172.28.0.7
function rand(){
    min=$1
    max=$(($2-$min+1))
    num=$(($RANDOM+1000000000)) #添加一个10位的数再求余
    echo $(($num%$max+$min))
}
port=$(rand 10000 50000)
step=20000

DATADIR=/home/tank/cys/rhythm/BE/cnn-bench/CnnBenchProgress/cnn_appinfo

ps_pid=0
# ps_pid=$(docker exec -i Tensor-PS ps aux|grep tf_cnn_benchmarks|grep -v grep|awk '{print $2}')
if [[ "$ps_pid" && "$ps_pid" != "1" ]]
then
    echo "PS has exited"
else
    echo "Start PS"
    docker exec -e CUDA_VISIBLE_DEVICES=-1 -i Tensor-PS python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=32 --model=resnet20 --print_training_accuracy=True --num_batches=$step --job_name=ps --ps_hosts=$ps:$port --worker_hosts=$worker1:$port,$worker2:$port --task_index=0  --cross_replica_sync=False --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> /dev/null 2>&1 &
fi

echo "Start Work-1"
docker exec -e CUDA_VISIBLE_DEVICES=-1 -i Tensor-Worker-1 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=32 --model=resnet20 --print_training_accuracy=True --num_batches=$step --job_name=worker --ps_hosts=$ps:$port --worker_hosts=$worker1:$port,$worker2:$port --task_index=0 --cross_replica_sync=False --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> /dev/null 2>&1 &
echo "Start Work-2"
docker exec -e CUDA_VISIBLE_DEVICES=-1 -i Tensor-Worker-2 python /root/benchmarks-master/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py --data_format=NHWC --batch_size=32 --model=resnet20 --print_training_accuracy=True --num_batches=$step --job_name=worker --ps_hosts=$ps:$port --worker_hosts=$worker1:$port,$worker2:$port --task_index=1 --cross_replica_sync=False --data_name=cifar10 --data_dir=/root/cifar-10-batches-py >> /dev/null 2>&1 &
echo "Running"
sleep 3
echo "开始获取训练任务步数以及Loss值"
if [ ! -f "${DATADIR}/$1.txt" ];then
  echo "Step-Loss数据写入文件:$1.txt"
else
  echo "删除旧数据文件"
  rm -f ./$1.txt
fi

docker exec -i Tensor-Worker-1 bash outloss.sh | tee -a ${DATADIR}/$1.txt
