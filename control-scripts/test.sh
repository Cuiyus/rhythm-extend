#!/usr/bin/env bash
function rand(){
    min=$1
    max=$(($2-$min+1))
    num=$(($RANDOM+1000000000)) #添加一个10位的数再求余
    echo $(($num%$max+$min))
}
port=$(rand 10000 50000)
echo $port
