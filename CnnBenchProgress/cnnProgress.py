import numpy as np
from scipy.optimize import curve_fit
import os, re, time
import subprocess, threading

'''
功能；
1. 对分布式同步训练任务的监控及进度刻画以及实现
2. web触发式查询
未完成：
 -- 1. 缺乏控制程序
2. 目前只能获取同步任务，缺乏对异步任务，非分布式任务的监控
'''

class cnnProgress(object):
    def __init__(self):
        self.appDict = set()
        # 用于存储AI的任务进度等信息,["11115",0.047367773968495654,"AI"]
        self.priority = []
        self.lock = threading.RLock()
        self.appProgress = []


    def refreshAppDict(self, data):
        try:
            self.lock.acquire()
            self.appDict.clear()
            self.appDict = self.appDict.union(data)
        finally:
            self.lock.release()

    def refreshPriority(self):
        try:
            self.lock.acquire()
            self.priority.clear()
            self.priority = self.priority + self.appProgress
        finally:
            self.lock.release()

    def getAppDict(self):
        while True:
            cmd = ["docker", "exec", "-i", "Tensor-Worker-1", "bash", "/root/outins.sh"]
            info = subprocess.run(cmd, stdout=subprocess.PIPE)
            insInfo = info.stdout.decode('utf-8').split('\n')
            appinfo = set()
            if len(insInfo) == 0:
                print("没有正在运行的训练任务")
                return None
            else:
                for d in insInfo:
                    insIdPat = re.compile(r'TCP \*:(\d{4,5}) \(LISTEN\)') # 端口号
                    insPidPat = re.compile(r'tf_cnn_be (\d{3,5}) root') # 进程ID
                    insId = insIdPat.findall(d)
                    insPid = insPidPat.findall(d)
                    if len(insId) != 0 and len(insPid) != 0:
                        appinfo.add((insId[0], insPid[0]))
            self.refreshAppDict(appinfo)

    def getProgress(self, app):
        path = "/home/tank/cys/rhythm/BE/cnn-bench/CnnBenchProgress/cnn_appinfo/{}.txt".format(app[0])
        totalStep, endstep, progress = stepPredict(optimusFunc, path, 0.22)
        self.appProgress.append([app[0], progress, "AI"])


    def Priority(self):
        while True:
            self.appProgress = []
            progress_thread = []
            for app in list(self.appDict):
                t = threading.Thread(target=self.getProgress, args=(app,))
                t.start()
                progress_thread.append(t)
            for p in progress_thread:
                p.join()

            self.refreshPriority()
            self.priority.sort(key=lambda x: x[1], reverse=False)

    def run(self):
        updateappDict = threading.Thread(target=self.getAppDict)
        pri = threading.Thread(target=self.Priority)
        updateappDict.start()
        pri.start()


def optimusFunc(step, a, b, c):
    return np.power(a * step + b, -1) + c

def stepPredict(func, data_path, loss):
    '''
    :param func: Optimus精度计算公式
    :param data_path: Cnn-bench训练任务的stop与loss
    :param loss: 指定精度
    :return: 精度计算公式中的a,b,c
    '''
    step_loss = []
    with open(data_path, 'r') as f:
        line = f.readline()
        while line:
            line = line.strip('\n')
            step_loss.append(line.split("\t"))
            line = f.readline()
    x = [int(d[0]) for d in step_loss]
    y = [float(d[1]) for d in step_loss]
    if len(x)==0 and len(y) ==0 :
        return None,None,None
    popt, pcov = curve_fit(func, x[:], y[:], bounds=(0, [3., 1., 0.19]))
    # popt, pcov = curve_fit(func, x[1000], y, bounds=(0, [3., 1., 0.19]))
    a, b, c = popt[0], popt[1], popt[2]
    totalStep =  1/((loss - c) * a) - (b/a)
    progress = x[-1] / totalStep
    return totalStep, x[-1], progress




from flask import Flask, jsonify
app = Flask(__name__)
@app.route("/getPriority", methods=["GET"])
def getPriority():
    cnn = cnnProgress()
    cnn.run()
    job_order = {}
    if cnn.priority:
        for i, app in enumerate(cnn.priority):
            job_order[i] = app
            print(app)
    return jsonify(job_order)
@app.route("/index", methods=["GET"])
def index():
    return "启动成功"

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=10088)


