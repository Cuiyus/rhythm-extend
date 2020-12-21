import time, subprocess
import threading, re
# import mysql.connector
# from initDB import initDB
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


# Scimark启动样例
# 需要为Scimark启动容器
'''
相当于一个不可预测队列：
web中视图函数返回的

整体思路：
类：scimarkHandler(FileSystemEventHandler) 用来监控实时scimark日志文件；
方法：def monitorscimark(appdict)捕获已启动的scimark任务的pid以及启动时间戳
服务时间查询：
1.设置interrupt环境变量作为查询信号，当interrupt变为True，程序记录运行时间以及资源量
2.使用Webserver

未实现的功能：
缺乏对scimark的控制操作
'''


class scimarkHandler(FileSystemEventHandler):
    def __init__(self, appdict):
        super(scimarkHandler,self).__init__()
        self.appdict = appdict
        self.lock = threading.RLock()
    def on_modified(self, event):
        if event.src_path == "/home/tank/cys/rhythm/BE/scimark/SerTime/Scimark/scilog/sci.log":
            with open(event.src_path,'r+') as f:
                last_lines = f.readlines()[-1]
                info = last_lines.strip("\n").split(" ")
                # self.info.append(info)
                pid, startTime = info[0], info[1]
                self.lock.acquire()
                try:
                    self.appdict.add((pid, startTime))
                finally:
                    self.lock.release()


import Pyro4
@Pyro4.expose
class scimarkProgress(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.appDict = set()
        self.event_handler = None
        self.observer = None
        self.path = r"/home/tank/cys/rhythm/BE/scimark/SerTime/Scimark/scilog/sci.log"

    def sciRecord(self):
        '''
        监控scimark，当有新的scimark任务
        参数：appdict[pid:[starttime,]] 存储了已启动的scimark的pid与启动时间戳
        :return:
        '''
        self.observer.schedule(self.event_handler, path=self.path, recursive=False)
        self.observer.start()
        try:
            while True:
                # update
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    #监控Scimark的活跃进程
    def appisAlive(self, pid):
        cmd = "docker exec -i Scimark ps aux | grep {}".format(pid)
        info = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        info = info.stdout.decode("utf-8")
        if info:
            return True
        else:
            return False

    def monitorAppIsAlive(self):
        while True:
            for app in list(self.appDict):
                if not self.appisAlive(app[0]):
                    self.lock.acquire()
                    try:
                        self.appDict.discard(app)
                    finally:
                        self.lock.release()

    def run(self):
        rec = threading.Thread(target=self.sciRecord)
        mon = threading.Thread(target=self.monitorAppIsAlive)
        rec.start()
        mon.start()

def resource(Container_name):
    '''
    获取容器资源数量（CPU）
    :return:
    '''
    cpunum = 0
    cmd = "docker inspect {}|grep CpusetCpus ".format(Container_name)
    info = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    info = info.stdout.decode("utf-8")
    cpupat = re.compile('"CpusetCpus": "(.*)"')
    cpuinfo = cpupat.findall(info)[0]
    if ',' in cpuinfo and "-" not in cpuinfo : cpunum = len(cpuinfo.split(","))
    elif "," not in cpuinfo and "-" in cpuinfo:
        n,m = list(map(lambda x : int(x), cpuinfo.split("-")))
        cpunum = m - n + 1
    elif "," and "-" in cpuinfo:
        num = cpuinfo.split(",")
        for n in num:
            n, m = list(map(lambda x: int(x), n.split("-")))
            cpunum += (m - n + 1)
    return cpunum


from flask import Flask,jsonify
app = Flask(__name__)

@app.route("/getSertime", methods=["GET"])
def getSertime():
    '''
    :return:返回的scimark任务的服务时间序列（降序）： 运行时间（ms） * CPU数量
    '''
    sertimeInfo = {}
    # for pid in hpc_appdict:
    for app in sci.appDict:
        localtime = int(time.time()*1000) # 毫秒
        cpunum = resource("Scimark")
        sertime = (localtime - int(app[1])) / 1000
        sertimeInfo[app[0]] = [app[1], sertime * cpunum]
    return jsonify(sertimeInfo)

@app.route("/index", methods=["GET"])
def index():
    return "启动成功"

if __name__ == '__main__':
    sci = scimarkProgress()
    sci.event_handler = scimarkHandler(sci.appDict)
    sci.observer = Observer()
    sci.run()
    app.run(host="0.0.0.0",port=10086)