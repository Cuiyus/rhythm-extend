from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time, subprocess
import threading, re
import numpy as np
from scipy.optimize import curve_fit

'''
生成两个队列，可预测与不可预测
可预测：AI与Spark
不可预测：SCIMARK
'''
# SCIMARK
from HpccProgress.SerTime import scimarkProgress, scimarkHandler, Observer
from HpccProgress.SerTime import resource
sci = scimarkProgress()
sci.event_handler = scimarkHandler(sci.appDict)
sci.observer = Observer()
sci.run()

# Spark
from SparkProgress.spiderForSpark import sparkProgress
saprk = sparkProgress("192.168.1.106")

# AI
from CnnBenchProgress.cnnProgress import cnnProgress
cnn = cnnProgress()


from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/getPriority', methods=["GET"])
def getPriority():
    # sci
    unpredict = {}
    for pid in sci.appDict:
        localtime = int(time.time()*1000) # 毫秒
        cpunum = resource("Scimark")
        sertime = (localtime - int(sci.appDict[pid][0])) / 1000
        sci.appDict[pid].append([sertime, cpunum])
        unpredict[pid] = sertime * cpunum
    return unpredict
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10089)