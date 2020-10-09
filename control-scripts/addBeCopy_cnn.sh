#!/usr/bin/env bash
# 放置于Tensor-Worker-1
DATADIR=/share
function rand(){
min=$1
max=$(($2-$min+1))
    num=$(($RANDOM+1000000000)) #添加一个10位的数再求余
        echo $(($num%$max+$min))
}
port=$(rand 10000 50000)
parallel-ssh -h /root/hosts -i bash runcnn.sh $port &
bash /root/runcnn.sh $port
bash /root/outloss.sh $port >> ${DATADIR}/$port.txt &
wait