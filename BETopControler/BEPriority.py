
import time
import sys
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

# 启动Spark监控，每一秒更新一次spark的任务信息
from SparkProgress.spiderForSpark import sparkProgress
spark = sparkProgress("192.168.1.106")
spark.run()

# 启动AI监控，每一秒更新一次AI的任务信息
from CnnBenchProgress.cnnProgress import cnnProgress
cnn = cnnProgress()
cnn.run()

# Killer
from BETopControler.controlkiller import killer
killer = killer()

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
            anw = p[0]
            return ['predict', anw]
        elif unp[0][1] == p[0][1]:
            anw = p[0]
            return ['predict', anw]
        elif unp[0][1] < p[0][1]:
            anw = unp[0]
            return ['unpredict', anw]

def getHpccPriority(hpcc):
    '''
    :param hpcc: scimark的监控对象
    :return:
    sciAppdict 存储有scimark信息的字典 -- 方便转换为json传递
    unpredict 存储有scimark信息的列表,以按照服务时间排序 -- 方便优先级排序
    '''
    sciAppdict = {}
    unpredict = []
    for i, pid in enumerate(hpcc.appDict):
        localtime = int(time.time() * 1000)  # 毫秒
        cpunum = resource("Scimark")
        sertime = (localtime - int(hpcc.appDict[pid][0])) / 1000
        sciAppdict[i] = [pid, sertime * cpunum, "sci"]
        unpredict.append([pid, sertime * cpunum, "sci"])
    maxSertime = max(sciAppdict.items(), key=lambda x: x[1][1])[1][1]
    for app in unpredict: app[1] = app[1] / maxSertime
    unpredict.sort(key=lambda x:x[1], reverse=False)
    return sciAppdict, unpredict


from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/getSparkJob',methods=["GET"])
def getSparkJob():
    return jsonify(spark.appDict)

@app.route('/getAIJob',methods=["GET"])
def getAIJob():
    return jsonify(cnn.appDict)

@app.route('/getPriority', methods=["GET"])
def getPriority():
    '''
    返回一个json字符串：{kill: [appname,progress,apptype]}
    :return:
    '''
    # 不同类型任务的priority=[appid,Sertime[/progress]]
    # sci
    predict_appinfo = {}

    t0 = int(time.time() * 1000)
    # 获取存储有scimark不可预测任务信息的队列
    unpredict_appinfo, unpredict_priority = getHpccPriority(sci)
    # spark and ai
    t1 = int(time.time() * 1000)
    # spark.Priority()
    # t2 = int(time.time() * 1000)
    # cnn.Priority()
    t3 = int(time.time() * 1000)
    print("Sci:{}".format((t1-t0)))
    # 获取存储有AI与spark不可预测任务信息的队列
    predict_priority = spark.priority + cnn.priority
    predict_priority.sort(key=lambda x: x[1], reverse=False)
    for i,d in enumerate(predict_priority):
        predict_appinfo[i] = d
    t4 = int(time.time() * 1000)
    print("Sort priority {}".format(t4-t3))
    print("AI appdict", cnn.appDict)
    print("Spark appdict", spark.appDict)

    # unk = MultiQueue(unpredict, "unpredict")
    # k = MultiQueue(predict,"predict")

    pick_job = pickJob(unpredict_priority, predict_priority)
    kill_job = None
    if pick_job:
        if pick_job[0] == "predict": kill_job = predict_appinfo.get(0)
        else:kill_job = unpredict_appinfo.get(0)
    else:
        return "没有BE任务在运行"

    all_info = {}
    all_info["predict"] = predict_appinfo
    all_info["unpredict"] = unpredict_appinfo
    all_info["kill"] = kill_job

    killer.job_info = kill_job
    killer.operating()

    return jsonify(all_info)


app.run(host="0.0.0.0", port=10089)