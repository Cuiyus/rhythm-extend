"""有序启动混合类型BE"""
import subprocess
from flask import Flask, jsonify, request, Response
from threading import Thread
import time, sys
import configparser
import Pyro4, json
from copy import deepcopy
import logging, threading
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
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
    global activeJobInfo
    sciapp = list(sci.getAppDict())
    sparkapp = list(spark.getAppDict())
    cnnapp = list(cnn.getAppDict())
    app = sciapp + sparkapp + cnnapp
    activeOrder = []
    for i in app:
        if i in activeJobInfo.values():
            order = list(activeJobInfo.keys())[list(activeJobInfo.values()).index(i)]
            activeOrder.append(order)
    activeOrder.sort()
    return activeOrder


def killBE():
    '''
    kill all BE
    :return:
    '''
    global tmp, rescheduBe
    global activeJobInfo
    global scicount, cnncount, sparkcount
    orders = refreshActiveJob()
    path = cfg.get("Experiment","log")
    print(orders)
    if orders:
        app = "--".join([tmp[i] for i in orders])
        rescheduBe = [tmp[i] for i in orders]
        form = "Current activeJob's(ReschdeuBe) Order: {}  App:{}\n"
        with open(path, "a+") as f:
            print("----"*10, file=f)
            f.write(form.format(str(orders),app))
    activeJobInfo.clear()
    cmd1 = "docker exec -i Tensor-Worker-1 bash /home/tank/killAll.sh "
    cmd2 = "docker exec -i Spark-1 bash /home/tank/killAll.sh"
    cmd3 = "docker exec -i Scimark bash /home/tank/killAll.sh"
    subprocess.run(cmd1, shell=True)
    subprocess.run(cmd2, shell=True)
    subprocess.run(cmd3, shell=True)
    scicount, sparkcount, cnncount = 0, 0, 0

def launchBE(be, order):
    path = cfg.get("Experiment", "log")
    global appbak
    timeout =3
    global launchOrder
    global activeJobInfo
    global scicount, cnncount, sparkcount
    with open(path, "a+") as f:
        print('----'*10, file=f)
        print("Curren Launch {}th job {}\n".format(order,be), file=f)
    f = open(path, 'a+')
    if be == "AI":
        cnncount += 1
        step = cfg.get("AI", 'step')
        launchOrder[order] = "AI"
        ai = Thread(target=launchAi, args=(step,))
        ai.start()
        cnnappdict = cnn.getAppDict()
        while ((not cnnappdict) or (len(cnnappdict) != cnncount)):
            cnnappdict = cnn.getAppDict()
            time.sleep(1)
        print("----------------------------------------", file=f)
        print(cnncount, file=f)
        print(cnnappdict, file=f)
        print("-----------------------------------------", file=f)
        info = cnnappdict - (cnnappdict & appbak)
        activeJobInfo[order] = list(info)[0]
        appbak = appbak.union(info)
        return "Start AI"
    elif be == "KMeans":
        sparkcount += 1
        launchOrder[order]= "Kmeans"
        kmeans = Thread(target=launchSpark, args=(be,))
        kmeans.start()
        sparkappdict = spark.getAppDict()
        while ((not sparkappdict) or (len(sparkappdict) != sparkcount)):
            sparkappdict = spark.getAppDict()
            time.sleep(1)
        print("----------------------------------------", file=f)
        print(sparkcount, file=f)
        print(sparkappdict, file=f)
        print("-----------------------------------------", file=f)
        info = sparkappdict - (sparkappdict & appbak)
        activeJobInfo[order] = list(info)[0]
        appbak = appbak.union(info)
        return "Start KMeans"
    elif be == "LogisticRegression":
        sparkcount += 1
        launchOrder[order] = "LogisticRegression"
        lg = Thread(target=launchSpark, args=("LogisticRegression",))
        lg.start()
        sparkappdict = spark.getAppDict()
        while ((not sparkappdict) or (len(sparkappdict) != sparkcount)):
            sparkappdict = spark.getAppDict()
            time.sleep(1)
        print("----------------------------------------", file=f)
        print(sparkcount, file=f)
        print(sparkappdict, file=f)
        print("-----------------------------------------", file=f)
        info = sparkappdict - (sparkappdict & appbak)
        activeJobInfo[order] = list(info)[0]
        appbak = appbak.union(info)
        return "Start LogisticRegression"
    elif be == "Hpcc":
        scicount += 1
        launchOrder[order] = "hpcc"
        hpcc = Thread(target=launchHpcc)
        hpcc.start()
        time.sleep(timeout)
        sciappdict = sci.getAppDict()
        while ((not sciappdict) or (len(sciappdict) != scicount)):
            sciappdict = sci.getAppDict()
            time.sleep(1)
        print("----------------------------------------", file=f)
        print(scicount, file=f)
        print(sciappdict, file=f)
        print("-----------------------------------------", file=f)
        info = sciappdict - (sciappdict & appbak)
        activeJobInfo[order] = list(info)[0]
        appbak = appbak.union(info)
        return "Start Hpcc"
    f.close()


def launch(arriveBe, type):
    global rescheduBe
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
        order = 0
        print("开始启动 ResBe内的任务")
        while rescheduBe:
            try:
                job = rescheduBe.pop(0)
                threading.RLock.acquire()
            finally:
                threading.RLock.release()
            yield launchBE(job, order)
            order += 1

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
@app.route("/getActiveBe", methods=["GET",])
def getActiveBe():
    return jsonify(activeJobInfo)

@app.route("/getActiveOrder", methods=["GET",])
def getActiveOrder():
    order = refreshActiveJob()
    orderinfo = {"order": order}
    return jsonify(orderinfo)
@app.route("/getJobNum", methods=["GET",])
def getJobNum():
    info = {"sci":scicount, "spark":sparkcount, "cnn":cnncount}
    return jsonify(info)
if __name__ == '__main__':
    arriveBe = cfg.get("Experiment", "arriveBe").split(",")
    arriveBe = list(map(lambda x: x.strip(), arriveBe))
    tmp = arriveBe.copy()
    rescheduBe = [] # 想要用字典保存任务启动的序号
    launchOrder = {}
    activeJobInfo = {}
    global loader
    # type：loop type：fixed（6）
    loader = launch(arriveBe, cfg.get("Experiment", "type"))

    # 应用集合备份
    appbak = set()
    # 应用启动计数器
    scicount = 0
    cnncount = 0
    sparkcount = 0

    # 清空日志内容
    path = cfg.get("Experiment", "log")
    with open(path, "wb+") as f: f.truncate()
    app.run(host="0.0.0.0", port=10081)