#!/usr/bin/env bash
sparkApp=(KMenas LogisticRegression)
function parity() {
    local random=$1
    if [ $[$random%2] -eq 0 ]
    then
      return 0;
    else
      return 1;
    fi

}
function test() {
    echo $1
}
parity $RANDOM
bash /root/spark-bench-legacy/bin/submit_job.sh ${sparkApp[$?]}