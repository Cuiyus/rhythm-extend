import requests
import time,re
import subprocess
from multiprocessing import Pool, process
import threading, configparser
from bs4 import BeautifulSoup
# from copy import deepcopy
import logging
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
'''
刻画不同spark的工作进度
已实现功能：
1. 每两秒刻画运行时的spark任务进度，非触发式的
2. 采集正在运行时的task启动时间,可用来计算kill操作的是loss
3. 修改为web触发式函数
'''
import Pyro4
@Pyro4.expose
class sparkProgress(object):
    def __init__(self, ip):
        # sparkui and rest IP
        self.ip = ip
        # sparkRestPort
        self.restport = 18080
        self.appDict = set()
        self.appProgress = []
        # spark aApplication Executor
        self.app_Executor = {}
        self.app_Executor_temp = {}

        # 用于存储spark的任务进度等信息,["application_1599144170737_0039", 0.06666666666666667, "spark"]
        self.priority = []
        self.lock = threading.RLock()

    def getAppDict(self):
        return self.getAppID_Port()

    def getExecutor(self):
        return self.app_Executor


    def reflashAppDict(self, data):
        '''
        如果不加锁的话
        RuntimeError: Set changed size during iteration
        :param data:
        :return:
        '''
        try:
            self.lock.acquire()
            self.appDict.clear()
            self.appDict = self.appDict.union(data)
        finally:
            self.lock.release()

    def getResponse(self, url):
        try:
            res = requests.get(url)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
        except requests.exceptions.HTTPError:
            # print("{} 任务未完成初始化 -- getProgress".format(app[0]))
            return None
        except requests.exceptions.ConnectionError:
            return None
        finally:
            return res

    def reflashPriority(self):
        try:
            self.lock.acquire()
            self.priority.clear()
            self.priority = self.appProgress
        finally:
            self.lock.release()

    def reflashAppExecutor(self):
        self.app_Executor.clear()
        self.app_Executor.update(self.app_Executor_temp)

    def getAppID_Port(self):
        url = "http://192.168.1.106:8088/ws/v1/cluster/apps?queue=default"
        trackingUrl = False
        appinfo = set()
        timeout = 5 # 如果5秒内还是无法查询到Spark任务的信息，则返回空集合
        while ((not trackingUrl) and timeout):
            apps = self.getResponse(url).json()["apps"]
            if apps:
                for i, app in enumerate(apps["app"]):
                    if "trackingUrl" not in app.keys():
                        appinfo.clear()
                        break
                    appinfo.add((app["id"], app["trackingUrl"]))
                    if i == (len(apps["app"]) - 1):
                        trackingUrl = True
            time.sleep(1)
            timeout -= 1
        self.reflashAppDict(appinfo)
        return appinfo

    def getProgress(self, appinfo):
        res = self.getResponse(appinfo[1])
        progress = {}
        running_job, compile_job, total_job = 0, 0, 0
        soup = BeautifulSoup(res.text.encode("utf-8"), 'lxml')
        try:
            activateJobInfo = soup.find("table", attrs={'id': "activeJob-table"}). \
                select('span[style="text-align:center; position:absolute; width:100%; left:0;"]')
            task_pat = re.compile(r'(\d{1,3})/(\d{1,3})')
            runningJobTaskInfo = task_pat.findall(activateJobInfo[0].string)[0]
            total_job += int(runningJobTaskInfo[1])
            running_job = int(runningJobTaskInfo[0])
            progress["progress"] = running_job / int(runningJobTaskInfo[1])
            self.appProgress.append([appinfo[0], progress["progress"], "spark"])
        except AttributeError as err:
            # print("completedJobInfo 未获取",err)
            pass
        except ZeroDivisionError as err:
            print("The spark Job提交后未完成任务初始化，Total Task= 0")
            self.appProgress.append([appinfo[0], 0.0, "spark"])
        return progress

    def getPriority(self):
        progress_thread = []
        self.appProgress = []
        applist = list(self.getAppDict())
        logger.info("此时Spark应用有：{}".format(applist))
        for app in applist:
            t = threading.Thread(target=self.getProgress, args=(app,))
            t.start()
            progress_thread.append(t)
        for t in progress_thread:
            t.join()
        self.reflashPriority()
        self.priority.sort(key=lambda x: x[1], reverse=False)
        logger.info("返回spark任务的优先级：{}".format(self.priority))
        return self.priority

    # getStageID，getRunningTask，getCoarseGrainedExecutorPort 都是针对单个spark application的类方法

    def getStageID(self, app, port=18080):
        '''
        :param ip:
        :param app:spark application_name/application_1599144170737_0017
        :param port:
        :return:此时正在运行的stageID
        '''
        url = "http://{0}:{1}/api/v1/applications/{2}/stages".format(self.ip, port, app)
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except requests.exceptions.HTTPError as err:
            print("访问失败{}".format(err))
            return None
        activeID = []
        stageinfo = response.json()
        for stage in stageinfo:
            if stage["status"] == "PENDING":
                activeID.append(stage["stageId"])
        if len(activeID) == 0:
            print("spark任务{}运行结束".format(app))
            return None
        activeID.sort()
        return activeID[0]

    def getRunningTask(self, app, stageID):
        '''
        :param app:
        :param stageid:activeID[0]
        :return: 正在运行的task的启动时间
        '''
        # "http://master:8088/proxy/application_1599144170737_0013/stages/stage/?id=0&attempt=0"
        url = "http://master:8088/proxy/{0}/stages/stage/?id={1}&attempt=0".format(app, stageID)
        runningtaskdata = []
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except requests.exceptions.HTTPError as err:
            print("无法获取任务{}的stage信息:{}".format(app, err))
            return None
        soup = BeautifulSoup(response.text.encode("utf-8"), 'lxml')
        table = soup.find_all("table")
        tasktable = table[2]
        taskinfo = tasktable.find_all('tr')
        for task in taskinfo:
            l = task.find_all('td')
            taskStatus = l[3].string
            if taskStatus == "RUNNING":
                taskid = l[1].string
                address = l[6].div.string
                startime = l[7].string
                startime = int(time.mktime(time.strptime(startime, '%Y/%m/%d %H:%M:%S'))) * 1000
                info = [taskid, taskStatus, address, startime]
                runningtaskdata.append(info)

        return runningtaskdata

    def getAppCoarseGrainedExecutorPort(self, app):
        url = "http://{0}:{1}/api/v1/applications/{2}/executors/".format(self.ip, self.restport, app[0])
        executorDict = []
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except requests.exceptions.HTTPError:
            # print("{} 任务未完成初始化 -- getAppCoarseGrainedExecutorPort".format(app[0]))
            return None
        # Spark Application Driver
        try:
            driver = response.json()[0]
        except IndexError:
            print("Nodriver")
        executor = response.json()[1:]
        for exe in executor:
            try:
                nodetype, port = exe["hostPort"].split(":")
                executorDict.append([nodetype, port])
            except ValueError as err:
                print(err)
                print(exe["hostPort"])
        try:
            self.lock.acquire()
            self.app_Executor_temp[app[0]] = executorDict
        finally:
            self.lock.release()

    def getAllExecutor(self):
        while True:
            # 有问题
            self.app_Executor_temp = {}
            progress_thread = []
            for app in list(self.appDict):
                t = threading.Thread(target=self.getAppCoarseGrainedExecutorPort, args=(app,))
                t.start()
                progress_thread.append(t)
            for t in progress_thread:
                t.join()
            self.reflashAppExecutor()

    def run(self):
        updateappExecutor = threading.Thread(target=self.getAllExecutor)
        updateappExecutor.start()



def rmiServer(spark, cfg):
    Pyro4.Daemon.serveSimple(
        {
            spark: "spark"
        },
        host=cfg.get("rmi", "ip"),  # IP地址
        port=int(cfg.get("rmi", "port")),  # 端口号
        ns=False,  # 命名服务
        verbose=True  #
    )

def readConfig():
    cfg = configparser.ConfigParser()
    cfgname = "../config/config.ini"
    cfg.read(cfgname, encoding='utf-8')
    return cfg

from flask import Flask,jsonify

app = Flask(__name__)
@app.route("/getSpark", methods=['GET'])
def getSpark():
    spark.getAppID_Port()
    return jsonify(spark.appDict)

@app.route('/getPriority', methods=["GET"])
def getPriority():
    '''
    如果要设置多个K级队列，则将job_order进行划分
    :return:
    '''
    app = spark.getAppID_Port()
    p = spark.getPriority()
    print("App",app)
    print("App dict",spark.appDict)
    job_order = {}
    for i, a in enumerate(p):
        job_order[i] = a
    return jsonify(job_order)
    # return {"job":app}

if __name__ == '__main__':
    spark = sparkProgress(ip="192.168.1.106")
    cfg = readConfig()
    print(cfg.get("rmi", "ip"))
    rmiServer(spark, cfg)
    app.run(host="0.0.0.0",port=10087)