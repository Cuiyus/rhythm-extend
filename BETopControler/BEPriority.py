from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time, subprocess
import threading, re
import numpy as np
from scipy.optimize import curve_fit
import sys, queue

sys.path.append(r"/home/tank/cys/rhythm/BE/rhythm-extend")
'''
生成两个队列，可预测与不可预测
可预测：AI与Spark
不可预测：SCIMARK


缺点：
kill job 每次决策时间为2秒，其中spark任务获取优先级时间最长大概在1.5秒
而三类任务的初始化
sci.run()
spark = sparkProgress("192.168.1.106")
cnn = cnnProgress()
共耗时10s，然后才能启动flask任务

优化策略：
1.对于三类任务的初始化，以及优先级队列获取修改为异步多线程
2.对于yarn 任务的获取，使用yarn rest接口
'''
# SCIMARK
from HpccProgress.SerTime import scimarkProgress, scimarkHandler, Observer, resource

sci = scimarkProgress()
sci.event_handler = scimarkHandler(sci.appDict)
sci.observer = Observer()
sci.run()

# Spark
from SparkProgress.spiderForSpark import sparkProgress
spark = sparkProgress("192.168.1.106")

# AI
from CnnBenchProgress.cnnProgress import cnnProgress
cnn = cnnProgress()


def MultiQueue(priority, flag):
    '''
    划分为三级队列, 0-30%;30%-60%;60%-100%;
    :param priority:
    :return:
    '''
    k1, k2, k3 = [[] for x in range(3)]
    l = len(priority)
    if l == 0: return None
    elif l >= 1:
        if flag == "unpredict":
            # 字典升序排序按照服务时间
            maxSertime = max(priority.values())
            for k,v in priority.items():
                if 0 <= v < (0.3*maxSertime):
                    k1.append(k)
                elif (0.3*maxSertime) <= v < (0.6*maxSertime):
                    k2.append(k)
                else:
                    k3.append(k)
        if flag == "predict":
            for k,v in priority.items():
                if 0 <= v[1] < 0.3:
                    k1.append(v[0])
                elif 0.3 <= v[1] < 0.6:
                    k2.append(v[0])
                else:
                    k3.append(v[0])
    return [k1,k2,k3]

def pickJob(unk,k):
    '''
    在0%-60%之间
    :param unk:不可预测队列
    :param k: 可预测
    :return: 要被kill的任务
    '''
    if not unk and not k:
        return None
    elif unk and not k:
        anw = unk[0] + unk[1] + unk[2]
        return anw[0]
    elif not unk and k:
        anw = k[0] + k[1] + k[2]
        return anw[0]
    else:
        for i in range(3):
            k1 = k[0] + unk[0]
            k2 = k[1] + unk[1]
            k3 = unk[2] + k[2]
        if len(k1):
            return k1[0]
        elif len(k2) and len(k1)== 0:
            return k2[0]
        else:
            return k3[0]


from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/getPriority', methods=["GET"])
def getPriority():
    # 不同类型任务的priority=[appid,Sertime/progress]
    # sci
    unpredict = {}
    t0 = int(time.time() * 1000)
    for pid in sci.appDict:
        localtime = int(time.time()*1000) # 毫秒
        cpunum = resource("Scimark")
        sertime = (localtime - int(sci.appDict[pid][0])) / 1000
        unpredict[pid] = sertime * cpunum

    # spark and ai
    predict = {}
    t1 = int(time.time() * 1000)
    spark.Priority()
    t2 = int(time.time() * 1000)
    cnn.Priority()
    t3 = int(time.time() * 1000)
    print("Sci:{} Spark:{} CNN:{}".format((t1-t0),(t2-t1),(t3-t2)))
    priority = spark.priority + cnn.priority
    priority.sort(key=lambda x: x[1], reverse=False)
    for i,d in enumerate(priority):
        predict[i] = d
    t4 = int(time.time() * 1000)
    print("Sort priority {}".format(t4-t3))

    unk = MultiQueue(unpredict, "unpredict")
    k = MultiQueue(predict,"predict")

    kill_job = pickJob(unk, k)

    all_info = {}
    all_info["predict"] = predict
    all_info["unpredict"] = unpredict
    all_info["kill"] = kill_job
    return jsonify(all_info)



app.run(host="0.0.0.0", port=10089)