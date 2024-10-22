# coding=utf-8
import time
import sys, Pyro4, random, logging
sys.path.append(r"/home/tank/cys/rhythm/BE/rhythm-extend")
from Preftest.perftime import MyTimer
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import configparser
def readConfig():
    cfg = configparser.ConfigParser()
    cfgname = "../config/config.ini"
    cfg.read(cfgname, encoding='utf-8')
    return cfg
cfg =readConfig()
# SCIMARK
from HpccProgress.SerTime import scimarkProgress, scimarkHandler, Observer, resource
sci = scimarkProgress()
sci.event_handler = scimarkHandler(sci.appDict)
sci.observer = Observer()
def startHPCMonitor(sci):
    sci.run()
    print("Start HPCMonitor")

# 启动Spark监控，每一秒更新一次spark的任务信息
from SparkProgress.spiderForSpark import sparkProgress
spark = sparkProgress(cfg.get("SPARK", "ip"))
def startSparkMonitor(spark):
    spark.run()
    print("Start SparkMonitor")

# 启动AI监控，每一秒更新一次AI的任务信息
from CnnBenchProgress.cnnProgress import cnnProgress
cnn = cnnProgress()
def startAIMonitor(cnn):
    cnn.run()
    print("Start CnnMonitor")

# 构建Rmi调用
def rmiServer(sci, spark, cnn, cfg):
    Pyro4.Daemon.serveSimple(
        {
            sci: 'sci',  # 需要代理的类
            spark: "spark",
            cnn:"cnn"
        },
        host=cfg.get("rmi", "ip"),  # IP地址
        port=int(cfg.get("rmi", "port")),  # 端口号
        ns=False,  # 命名服务
        verbose=True  #
    )
    # daemon = Pyro4.Daemon()
    # uri_sci = daemon.register(sci)
    # uri_spark = daemon.register(spark)
    # uri_cnn = daemon.register(cnn)
    # ns = Pyro4.locateNS()
    # ns.register("sci", uri_sci)
    # ns.register("spark", uri_spark)
    # ns.register("cnn", uri_cnn)
    # daemon.requestLoop()

def MultiQueue(priority, flag):
    '''
    :param priority:
    :return:
    '''
    k1, k2, k3 = [[] for x in range(3)]
    l = len(priority)
    if l == 0: return None
    elif l >= 1:
        if flag == "unpredict":
            # 字典升序排序按照服务时间
            maxSertime = max(priority.items(), key=lambda x:x[1][1])[1][1]
            for k,v in priority.items():
                if 0 <= v[1] < (0.3*maxSertime):
                    k1.append(k)
                elif (0.3*maxSertime) <= v[1] < (0.6*maxSertime):
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

def pickJob(unp,p):
    '''
    :param unp:不可预测队列
    :param p: 可预测
    :return: 要被kill的任务
    '''
    if not unp and not p:
        return None
    elif unp and not p:
        anw = unp[0]
        return ['unpredict',anw]
    elif not unp and p:
        anw = p[0]
        return ['predict',anw]
    else:
        if unp[0][1] > p[0][1]:
            print(unp[0],p[0])
            anw = p[0]
            return ['predict', anw]
        elif unp[0][1] == p[0][1]:
            print(unp[0], p[0])
            anw = p[0]
            return ['predict', anw]
        elif unp[0][1] < p[0][1]:
            print(unp[0], p[0])
            anw = unp[0]
            return ['unpredict', anw]

def randomPick(unp,p):
    if not unp and not p:
        return None
    elif unp and not p:
        i = random.randint(0, len(unp)-1)
        anw = unp[i]
        return ['unpredict',anw]
    elif not unp and p:
        i = random.randint(0, len(p)-1)
        anw = p[i]
        return ['predict',anw]
    else:
        i = random.randint(0, 100)
        if (i/2)==0:#选择可预测队列
            j = random.randint(0, len(p)-1)
            return ['predict', p[j]]
        else:
            j = random.randint(0, len(unp)-1)
            return ['predict', unp[j]]

def getHpccPriority(hpcc):
    '''
    :param hpcc: scimark的监控对象
    :return:
    sciAppdict 存储有scimark信息的字典 -- 方便转换为json传递
    unpredict 存储有scimark信息的列表,以按照服务时间排序 -- 方便优先级排序
    '''
    sciAppdict = {}
    unpredict = []
    for i, pidinfo in enumerate(list(hpcc.getAppDict())):
        localtime = int(time.time() * 1000)  # 毫秒
        cpunum = resource("Scimark")
        sertime = (localtime - int(pidinfo[1])) / 1000
        sciAppdict[i] = [pidinfo[0], sertime * cpunum, "sci"]
        unpredict.append([pidinfo[0], sertime * cpunum, "sci"])
    if sciAppdict: maxSertime = max(sciAppdict.items(), key=lambda x: x[1][1])[1][1]
    for app in unpredict: app[1] = app[1] / maxSertime
    unpredict.sort(key=lambda x:x[1], reverse=False)
    return sciAppdict, unpredict

def getAllPriority(sci, spark, cnn):
    predict_appinfo = {}
    with MyTimer("挑选不可预测任务", logger):
        unpredict_appinfo, unpredict_priority = getHpccPriority(sci)
    # 获取存储有AI与spark不可预测任务信息的队列
    with MyTimer("挑选不可预测任务", logger):
        predict_priority = spark.getPriority() + cnn.getPriority()
    predict_priority.sort(key=lambda x: x[1], reverse=False)
    for i, d in enumerate(predict_priority):
        predict_appinfo[i] = d
    pick_job = pickJob(unpredict_priority, predict_priority)
    kill_job = None
    if pick_job:
        if pick_job[0] == "predict":
            kill_job = predict_appinfo.get(0)
        else:
            kill_job = unpredict_priority[0]
    else:
        print("没有BE任务在运行")
    return kill_job

def pickRandom(sci, spark, cnn):
    predict_appinfo = {}
    unpredict_appinfo, unpredict_priority = getHpccPriority(sci)
    # 获取存储有AI与spark不可预测任务信息的队列
    predict_priority = spark.priority + cnn.priority
    for i, d in enumerate(predict_priority):
        predict_appinfo[i] = d
    pick_job = randomPick(unpredict_priority, predict_priority)
    kill_job = None
    if pick_job:
        if pick_job[0] == "predict":
            kill_job = predict_appinfo.get(0)
        else:
            kill_job = unpredict_priority[0]
    else:
        print("没有BE任务在运行")
    return kill_job


import threading
def Monitorinit():
    threads = []
    # sparkmonitor_thread = threading.Thread(target=startSparkMonitor, args=(spark,))
    # sparkmonitor_thread.start()
    # aimonitor_thread = threading.Thread(target=startAIMonitor,args=(cnn,))
    # aimonitor_thread.start()
    hpcmonitor_thread = threading.Thread(target=startHPCMonitor, args=(sci,))
    hpcmonitor_thread.start()
    hpcmonitor_thread.join()
    # threads.extend([sparkmonitor_thread, aimonitor_thread, hpcmonitor_thread])
    # for t in threads:
    #     t.join()


from flask import Flask, jsonify, request
app = Flask(__name__)
# Launch Job
from Motivation.launcher import launcher
l = launcher(sci, spark, cnn)
@app.route('/launchmix', methods=["GET"])
def launchmix():
    global l
    try:
        return next(l.loader)
    except StopIteration:
        l.reload()
        return "重新读取任务列表"
@app.route("/getResBe", methods=["GET",])
def getrescheduBe():
    return jsonify(l.rescheduBe)
@app.route("/getLaunchBe", methods=["GET",])
def getlaunchedBe():
    return jsonify(l.launchOrder)
@app.route("/getActiveOrder", methods=["GET",])
def getActiveOrder():
    order = l.refreshActiveJob()
    orderinfo = {"order": order}
    return jsonify(orderinfo)
@app.route("/getJobNum", methods=["GET",])
def getJobNum():
    info = {"sci":l.scicount, "spark":l.sparkcount, "cnn":l.cnncount}
    return jsonify(info)
@app.route("/getAINum", methods=["GET",])
def getAINum():
    return str(l.cnncount)
@app.route("/getSparkNum", methods=["GET",])
def getSparkNum():
    return str(l.sparkcount)
@app.route("/getSciNum", methods=["GET",])
def getSciNum():
    # sciDict = {}
    # for i, app in enumerate(list(sci.getAppDict())): sciDict[i] = app
    # return jsonify(sciDict)
    return str(l.scicount)

# Get ActiveJob
@app.route('/getSparkJob',methods=["GET"])
def getSparkJob():
    sparkDict = {}
    for i, app in enumerate(list(spark.getAppDict())):sparkDict[i] = app
    return jsonify(sparkDict)

@app.route('/getAIJob',methods=["GET"])
def getAIJob():
    cnnDict = {}
    for i, app in enumerate(list(cnn.getAppDict())): cnnDict[i] = app
    return jsonify(cnnDict)

@app.route('/getSciJob',methods=["GET"])
def getSciJob():
    sciDict = {}
    for i, app in enumerate(list(sci.getAppDict())): sciDict[i] = app
    return jsonify(sciDict)

@app.route('/getActiveJob', methods=["GET"])
def getActiveJob():
    jobs = set()
    jobs.update(spark.getAppDict(), sci.appDict, cnn.appDict)
    info = {"jobs" : list(jobs), "Nums" : len(jobs)}
    return jsonify(info)

# Killer
from BETopControler.controlkiller import SparkKiller, AiKiller, HpcKiller

@app.route("/runkill",methods=["GET"])
def runkill():
    with MyTimer("从三类任务中挑选任务", logger):
        killjob = getAllPriority(sci, spark, cnn)
    if not killjob: return "没有正在运行的BE"
    if killjob[2] == "spark":
        worker = request.args.get("worker")
        if not worker:
            return "没有指定被kill的BE节点"
        killer = SparkKiller(spark=spark, job=killjob, worker=worker)
        killer.killExecutor()
        return "kill Spark Job {} Executor {} PID {}".format(killer.job[0], killer.node, killer.executorPid)
    elif killjob[2] == "AI":
        killer = AiKiller(job=killjob)
        killer.killsyncJob()
        return "kill Ai Job {}".format(killjob)
    elif killjob[2] == "sci":
        killer = HpcKiller(job=killjob)
        killer.killScimark()
        return "kill Hpc Job {}".format(killjob)

@app.route("/killrandom",methods=["GET"])
def killrandom():
    killjob = pickRandom(sci, spark, cnn)
    if not killjob: return "没有正在运行的BE"
    if killjob[2] == "spark":
        killer = SparkKiller(spark=spark, job=killjob, worker=None)
        killer.killApplication()
        return "kill Spark Application {}".format(killer.job[0])
    elif killjob[2] == "AI":
        killer = AiKiller(job=killjob)
        killer.killsyncJob()
        return "kill Ai Job {}".format(killjob)
    elif killjob[2] == "sci":
        killer = HpcKiller(job=killjob)
        killer.killScimark()
        return "kill Hpc Job {}".format(killjob)

@app.route("/killall", methods=["GET",])
def killall():
    k = threading.Thread(target=l.killBE)
    k.start()
    return "Start Kill"


if __name__ == '__main__':
    # cfg = readConfig()
    # rmi = threading.Thread(target=rmiServer, args=(sci, spark, cnn, cfg))
    # rmi.start()
    # print("rmi服务启动")

    Monitorinit()
    print("Flask启动")
    app.run(host="0.0.0.0", port=10089)
