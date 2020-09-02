#!/usr/bin/env bash
# 放到容器Spark-1（master）节点的目录下 /root/spark-bench-legacy/bin
DIR=`dirname "$0"`
DIR=`cd "${DIR}/.."; pwd`
SPARKBENCH=/root/spark-bench-legacy
func_submit(){
  local workload=$1
    echo -e "Exec script: $WORKLOAD/bin/run.sh"
    $WORKLOAD/bin/run.sh >> /dev/null 2&>1 &
    result=$?
    if [ $result -ne 0 ]
    then
      echo -e "ERROR: ${workload} failed to run successfully."
      exit $result
    fi
}
if [[ "$#" -eq 0 ]]; then
  echo "请输入以下应用名称：
# KMeans
# LinearRegression
# LogisticRegression
# SVM
# DecisionTree
# MatrixFactorization
# PageRank
# TriangleCount
# ShortestPaths
# LabelPropagation
# SVDPlusPlus
# ConnectedComponent
# StronglyConnectedComponent
# PregelOperation
# PCA
# SQL
# Streaming"
  exit
elif [ "$#" == "1" ] && [ "$1" == "all|ALL" ]; then
  for workload in `cat $DIR/bin/applications.lst`; do
    if [[ $workload == \#* ]]; then
        continue
    fi
    echo -e "$Prepare run ${workload} ..."
    WORKLOAD=${DIR}/${workload}
    func_submit ${workload}
    done
else
  for workload in "$@" ;do
    echo -e "$Prepare run ${workload} ..."
    WORKLOAD=${DIR}/${workload}
    func_submit ${workload}
  done
fi


