#!/usr/bin/env bash
sparkApp=(KMeans LogisticRegression)
function parity() {
    local random=$1
    if [ $[$random%2] -eq 0 ]
    then
      return 0;
    else
      return 1;
    fi

}
parity $RANDOM
bash /root/spark-bench-legacy/bin/submit_job.sh ${sparkApp[$?]}