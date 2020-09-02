import time, subprocess
import threading, re
# import mysql.connector
# from initDB import initDB
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


# Scimark启动样例
# 需要为Scimark启动容器
'''
整体思路：
类：scimarkHandler(FileSystemEventHandler) 用来监控实时scimark日志文件；
方法：def monitorscimark(appdict)捕获已启动的scimark任务的pid以及启动时间戳
服务时间查询：
1.设置interrupt环境变量作为查询信号，当interrupt变为True，程序记录运行时间以及资源量
2.使用Webserver
'''


class scimarkHandler(FileSystemEventHandler):
    def __init__(self, appdict):
        super(scimarkHandler,self).__init__()
        self.appdict = appdict
    def on_modified(self, event):
        if event.src_path == "/home/tank/cys/rhythm/BE/scimark/SerTime/Scimark/scilog/sci.log":
            with open(event.src_path,'r+') as f:
                last_lines = f.readlines()[-1]
                info = last_lines.strip("\n").split(" ")
                # self.info.append(info)
                pid, startTime = info[0], info[1]
                self.appdict[pid] = [startTime,]


def monitorscimark(appdict):
    '''
    监控scimark，当有新的scimark任务
    参数：appdict 存储了已启动的scimark的pid与启动时间戳
    :return:
    '''
    sci_event_handler = scimarkHandler(appdict)
    observer = Observer()
    path = r"/home/tank/cys/rhythm/BE/scimark/SerTime/Scimark/scilog/sci.log"
    observer.schedule(sci_event_handler, path=path, recursive=False)
    observer.start()
    try:
        while True:
            # update
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def appisAlive(pid):
    cmd = "docker exec -i Scimark ps aux | grep {}".format(pid)
    info = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    info = info.stdout.decode("utf-8")
    if info:
        return True
    else:
        return False

def resource():
    '''
    获取容器资源数量（CPU）
    :return:
    '''
    cpunum = 0
    cmd = "docker inspect {}|grep CpusetCpus ".format("Scimark")
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
    sertimeInfo = {}
    for pid in appdict:
        if appisAlive(pid):
            localtime = int(time.time()*1000) # 毫秒
            cpunum = resource()
            sertime = (localtime - int(appdict[pid][0])) / 1000
            appdict[pid].append([sertime, cpunum])
            sertimeInfo[pid] = sertime * cpunum

    return jsonify(sertimeInfo)


@app.route("/index", methods=["GET"])
def index():
    return "启动成功"

def test(appdict):
    while True:
        flag = input("是否")
        time.sleep(1)
        print(appdict)



global appdict
appdict = {}
monitor = threading.Thread(target=monitorscimark, args=(appdict,))
monitor.start()
app.run(host="0.0.0.0",port=10086)






