import numpy as np
from scipy.optimize import curve_fit
import os, re, time
import subprocess

'''
功能；
1. 对分布式同步训练任务的监控及进度刻画以及实现
2. web触发式查询
未完成：
1. 缺乏控制程序
2. 目前只能获取同步任务，缺乏对异步任务，非分布式任务的监控
'''
def getIns():
    cmd = ["docker", "exec", "-i", "Tensor-Worker-1", "bash", "/root/outins.sh"]
    info = subprocess.run(cmd, stdout=subprocess.PIPE)
    insInfo = info.stdout.decode('utf-8').split('\n')
    insDict = {}
    if len(insInfo) == 0:
        print("没有正在运行的训练任务")
        return None
    else:
        for d in insInfo:
            insIdPat = re.compile(r'TCP \*:(\d{4,5}) \(LISTEN\)')
            insPidPat = re.compile(r'tf_cnn_be (\d{3,5}) root')
            insId = insIdPat.findall(d)
            insPid = insPidPat.findall(d)
            if len(insId) != 0 and len(insPid) != 0:  insDict[insId[0]] = insPid[0]
        return insDict

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
        return None
    popt, pcov = curve_fit(func, x[:9000], y[:9000], bounds=(0, [3., 1., 0.19]))
    # popt, pcov = curve_fit(func, x[1000], y, bounds=(0, [3., 1., 0.19]))
    a, b, c = popt[0], popt[1], popt[2]
    totalStep =  1/((loss - c) * a) - (b/a)
    progress = x[-1] / totalStep
    return totalStep, x[-1], progress

def Priority():
    priority = []
    # while True:
    #     insDict = getIns()
    #     if insDict:
    #         print("有任务在运行")
    #         jobId = insDict.keys()
    #         break
    #     else:
    #         print("没有任务在运行")
    #         time.sleep(2)
    #         continue
    insDict = getIns()
    if insDict:
        print("有任务在运行")
        jobId = insDict.keys()
        for i in jobId:
            path = "/home/tank/cys/rhythm/BE/cnn-bench/CnnBenchProgress/cnn_appinfo/{}.txt".format(i)
            if stepPredict(optimusFunc, path, 0.22) is None:
                print("训练任务{}已提交,但未开始训练".format(i))
            else:
                totalStep, endstep, progress = stepPredict(optimusFunc, path, 0.22)
                priority.append([i, progress])

        priority.sort(key=lambda x: x[1], reverse=False)
        return priority
    else:
        print("没有任务在运行")
        return None



from flask import Flask, jsonify
app = Flask(__name__)
@app.route("/getPriority", methods=["GET"])
def getPriority():
    priority = Priority()
    job_order = {}
    if priority:
        for i, app in enumerate(priority):
            job_order[i] = app
    return jsonify(job_order)
@app.route("/index", methods=["GET"])
def index():
    return "启动成功"
app.run(host="0.0.0.0",port=10088)


# if __name__ == '__main__':
#     while True:
#         priority = Priority()
#         if priority:
#             job_order = [x[0] for x in priority]
#             for x in priority: x[1] = "{:.2f}%".format(float(x[1]) * 100)
#             print("Progress 动态队列:", priority)
#             time.sleep(2)
