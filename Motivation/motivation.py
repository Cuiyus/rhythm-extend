"""有序启动混合类型BE"""
import subprocess
from flask import Flask, jsonify, request, Response
from threading import Thread
import time, sys
import configparser
import Pyro4, json
from copy import deepcopy
import logging
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# class Topcontroller():
#     def __init__(self):
#         self.cfg = self.readcfg()
#     def readcfg(self):
#         cfg = configparser.ConfigParser()
#         cfgname = "config.ini"
#         cfg.read(cfgname, encoding='utf-8')
#         if len(cfg.sections()) == 0:
#             print("配置文件为空或者配置文件路径错误")
#             raise FileNotFoundError
#         return cfg
# 读取配置文件
def readConfig():
    cfg = configparser.ConfigParser()
    cfgname = "../config/config.ini"
    cfg.read(cfgname, encoding='utf-8')
    return cfg
cfg = readConfig()
# rmi client
ipAddressServer = cfg.get("rmi","ip")
spark = Pyro4.core.Proxy('PYRO:spark@' + ipAddressServer + ':9090')
sci = Pyro4.core.Proxy('PYRO:sci@' + ipAddressServer + ':9090')
cnn = Pyro4.core.Proxy('PYRO:cnn@' + ipAddressServer + ':9090')

# 用生成器来实现
file = r"/home/tank/cys/rhythm/BE/beleader-img/leader-volume/killtime.log"

def launchAi(step):
    cmd = "docker exec -i Tensor-Worker-1 bash /home/tank/addBeCopy_cnn.sh {}".format(step)
    subprocess.run(cmd, shell=True)

def launchSpark(be):
    cmd = "docker exec -i Spark-1 bash /root/spark-bench-legacy/bin/submit_job.sh {}".format(be)
    subprocess.run(cmd, shell=True)

def launchHpcc():
    cmd = "docker exec -i Scimark bash /home/tank/addBeCopy_cpu.sh  "
    subprocess.run(cmd, shell=True)

def refreshActiveJob():
    sciapp = list(sci.getAppDict())
    sparkapp = list(spark.getAppDict())
    cnnapp = list(cnn.getAppDict())

    app = sciapp + sparkapp + cnnapp
    activeOrder = []
    for i in app:
        if i in activeJobInfo:
            activeOrder.append(activeJobInfo[i])
    return activeOrder




def killBE():
    '''
    kill all BE
    :return:
    '''

    orders = refreshActiveJob()
    path = cfg.get("Experiment","log")
    print(orders)
    if orders:
        app = "--".join([tmp[i] for i in orders])
        rescheduBe = [tmp[i] for i in orders]
        form = "Current activeJob's(ReschdeuBe) Order: {}  App:{}\n"
        with open(path, "a+") as f:
            print("----"*10, '\n', file=f)
            f.write(form.format(str(orders),app))
            print("----" * 10, '\n', file=f)
    activeJobInfo.clear()
    cmd1 = "docker exec -i Tensor-Worker-1 bash /home/tank/killAll.sh "
    cmd2 = "docker exec -i Spark-1 bash /home/tank/killAll.sh"
    cmd3 = "docker exec -i Scimark bash /home/tank/killAll.sh"
    subprocess.run(cmd1, shell=True)
    subprocess.run(cmd2, shell=True)
    subprocess.run(cmd3, shell=True)


def launchBE(be, order):
    path = cfg.get("Experiment", "log")
    with open(path, "a+") as f:
        print('----'*10,'\n', file=f)
        print("Curren Launch {}th job {}\n".format(order,be), file=f)
        print('----'*10,'\n', file=f)
    if be == "AI":
        step = cfg.get("AI", 'step')
        cnnappdict = list(cnn.getAppDict())
        launchOrder[order] = "AI"
        if cnnappdict:
            activeJobInfo[cnnappdict[-1]] = order
        ai = Thread(target=launchAi, args=(step,))
        ai.start()
        return "Start AI"
    elif be == "KMeans":
        sparkappdict = list(spark.getAppDict())
        launchOrder[order]= "Kmeans"
        if sparkappdict:
            activeJobInfo[sparkappdict[-1]] = order
        kmeans = Thread(target=launchSpark, args=(be,))
        kmeans.start()
        return "Start KMeans"
    elif be == "LogisticRegression":
        sparkappdict = list(spark.getAppDict())
        launchOrder[order] = "LogisticRegression"
        if sparkappdict:
            activeJobInfo[sparkappdict[-1]] = order
        lg = Thread(target=launchSpark, args=("LogisticRegression",))
        lg.start()
        return "Start LogisticRegression"
    elif be == "Hpcc":
        sciappdict = list(sci.getAppDict())
        launchOrder[order] = "hpcc"
        if sciappdict:
            activeJobInfo[sciappdict[-1]] = order
        hpcc = Thread(target=launchHpcc)
        hpcc.start()
        return "Start Hpcc"


def launch(arriveBe, rescheduBe, type):
    if type == "loop":
        i = 0
        while True:
            if i == len(arriveBe): i = 0
            yield launchBE(arriveBe[i])
            i=i+1
            while rescheduBe: yield launchBE(rescheduBe.pop(0))

    elif type == "fix":
        order = 0
        while arriveBe:
            job = arriveBe.pop(0)
            yield launchBE(job, order)
            order += 1
        while rescheduBe:
            minorder = min(rescheduBe.keys())
            job = rescheduBe.pop(minorder)[0]
            yield launchBE(job, minorder)

app = Flask(__name__)
@app.route("/launchmix", methods=["GET",])
def launchmix():
    try:
        return next(loader)
    except StopIteration:
        return "没有后续任务待启动"
@app.route("/killall", methods=["GET",])
def killall():
    k = Thread(target=killBE)
    k.start()
    return "Start Kill"
@app.route("/killrandom", methods=["GET",])
def killrandom():
    pass
@app.route("/getResBe", methods=["GET",])
def getrescheduBe():
    return jsonify(rescheduBe)
@app.route("/getLaunchBe", methods=["GET",])
def getlaunchedBe():
    return jsonify(launchOrder)
if __name__ == '__main__':
    arriveBe = ["Hpcc", "AI", "KMeans",
              "Hpcc","AI", "LogisticRegression",
              "Hpcc","AI", "KMeans",
              "Hpcc", ]

    global tmp
    tmp = arriveBe.copy()

    global rescheduBe
    rescheduBe = [] # 想要用字典保存任务启动的序号

    global launchOrder
    launchOrder = {}

    global activeJobInfo
    activeJobInfo = {}

    global loader
    # type：loop type：fixed（6）
    loader = launch(arriveBe, rescheduBe, cfg.get("Experiment", "type"))

    # 清空日志内容
    path = cfg.get("Experiment", "log")
    with open(path, "wb+") as f: f.truncate()
    app.run(host="0.0.0.0", port=10081)