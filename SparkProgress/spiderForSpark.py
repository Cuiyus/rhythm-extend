import requests
import time,re
import subprocess
from multiprocessing import Pool, process
import threading
from bs4 import BeautifulSoup


'''
刻画不同spark的工作进度
已实现功能：
1. 每两秒刻画运行时的spark任务进度，非触发式的
2. 采集正在运行时的task启动时间,可用来计算kill操作的是loss
3. 修改为web触发式函数
还需实现：
-- 1. 控制操作为controlSpark.py 但未整合
2. 没有获取读取检查点的开销
代码缺陷：
1. spark的活跃任务实际上不需要事实监控：
    在 def getAppID_Port()函数中我们通过yarn application获取运行中的spark任务
    因此不需要在设置线程去实时监控更新活跃的spark任务 
'''
class sparkProgress(object):
    def __init__(self, ip):
        self.ip = ip
        self.appDict = set()

        # 用于存储spark的任务进度等信息,["application_1599144170737_0039", 0.06666666666666667, "spark"]
        self.priority = []
        self.lock = threading.RLock

    def reflashAppDict(self, data):
        try:
            self.lock.acquire()
            self.appDict.clear()
            self.appDict = self.appDict.union(data)
        finally:
            self.lock.acquire()


    def getAppID_Port(self):
        while True:
            t1 = int(time.time() * 1000)
            cmd = ["docker", "exec", "-i", "Spark-1", "yarn", "application", "-list"]
            yarninfo = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            info = yarninfo.stdout.decode('utf-8').split('\n')
            if len(info) > 2:
                data = info[2:]
                appinfo = set()
                for d in data:
                    appnamePat = re.compile(r"application_\d{13}_\d{4}")
                    appName = re.findall(appnamePat, d)
                    appPortPat = re.compile(r"http://master:(\d{4})")
                    appPort = re.findall(appPortPat, d)
                    # print(appId, appPort)
                    try:
                        if len(appName) != 0 and len(appPort) != 0:
                            # self.appDict[appId[0]] = appPort[0]
                            appinfo.add((appName[0], appPort[0]))
                    finally:
                        pass
                self.reflashAppDict(appinfo)
                t2 = int(time.time() * 1000)
                print("获取appDict的时间：{}".format((t2 - t1)))
                self.reflashAppDict(appinfo)


    def getProgress(self, app):
        # 使用了爬虫解析4040的spark页面
        '''
        :param res:
        :return:获取单个任务的工作进度
        '''
        url = "http://{0}:{1}".format(self.ip, app[1])
        try:
            res = requests.get(url)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
        except requests.exceptions.HTTPError:
            print("{} 任务未完成初始化".format(app[0]))
            return None
        except requests.exceptions.ConnectionError:
            print("任务：{} --- 连接错误".format(app[0]))
            return None

        soup = BeautifulSoup(res.text.encode("utf-8"), 'lxml')
        res1 = soup.select('span[style="text-align:center; position:absolute; width:100%; left:0;"]')
        progress = {}
        compilejob_info = {}
        running_job, compile_job = 0, 0
        task_pat = re.compile(r'(\d{1,3})/(\d{1,3})')
        for _ in res1:
            if "running" in str(_):
                running_job += 1
                p = task_pat.search(str(_))
                progress[running_job] = {}
                progress[running_job]["running_task"] = int(p.group(1))
                progress[running_job]["total_task"] = int(p.group(2))
            else:
                compile_job += 0
                p = task_pat.search(str(_))
                compilejob_info[compile_job] = {}
                compilejob_info[compile_job]["total_task"] = int(p.group(2))
                compilejob_info[compile_job]["progress"] = "100%"

        running_task = 0
        total_task = 0

        for task in progress.values():
            running_task += task["running_task"]
            total_task += task["total_task"]
        try:
            progress["progress"] = running_task / total_task
        except ZeroDivisionError:
            print("The spark Job提交后未完成任务初始化，Total Task= 0")
            return None

        self.priority.append([app[0], progress["progress"], "spark"])
        return progress

    def Priority(self):
        while True:
            progress_thread = []
            for app in self.appDict:
                t = threading.Thread(target=self.getProgress, args=(app,))
                t.start()
                progress_thread.append(t)
            for t in progress_thread:
                t.join()
            self.priority.sort(key=lambda x: x[1], reverse=False)


    def run(self):
        updateappDict = threading.Thread(target=self.getAppID_Port)
        updateappDict.start()
        priority = threading.Thread(target=self.Priority)
        priority.start()



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

    def getCoarseGrainedExecutorPort(self):
        url = "http://{0}:{1}/api/v1/applications/{2}/executors/".format(self.ip, self.port, self.jobinfo[0])
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except requests.exceptions.HTTPError:
            print("{} 任务未完成初始化".format(self.jobinfo[0]))
            return None
        # Spark Application Driver
        driver = response.json()[0]
        executor = response.json()[1:]
        for exe in executor:
            address, port = exe["hostPort"].split(":")
            self.executor_dict[address] = port






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
    spark.Priority()
    priority = spark.priority
    job_order = {}
    for i, app in enumerate(priority):
        job_order[i] = app
    return jsonify(job_order)

if __name__ == '__main__':
    spark = sparkProgress(ip="192.168.1.106")
    app.run(host="0.0.0.0",port=10087)