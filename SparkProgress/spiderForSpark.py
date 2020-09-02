import requests
import time,re
import subprocess
from multiprocessing import Pool, process
from bs4 import BeautifulSoup

'''
刻画不同spark的工作进度
'''

def getResponse(ip, port):
    url = "http://{0}:{1}".format(ip,port)
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response
    except requests.exceptions.HTTPError:
        print("{} 任务未完成初始化".format(ip))
        return None


def getAppID_Port():
    cmd = ["docker", "exec", "-i", "Spark-1","yarn", "application", "-list"]
    yarninfo = subprocess.run(cmd, stdout=subprocess.PIPE)
    info = yarninfo.stdout.decode('utf-8').split('\n')
    appDict = {}
    if len(info) > 2:
        data = info[2:]
        for d in data:
            appIdPat = re.compile(r"application_\d{13}_\d{4}")
            appId = re.findall(appIdPat, d)
            appPortPat = re.compile(r"http://master:(\d{4})")
            appPort = re.findall(appPortPat, d)
            # print(appId, appPort)
            if len(appId) != 0 and len(appPort) !=0 :  appDict[appId[0]] = appPort[0]
    else:
        print("没有正在运行的Spark任务")
        return
    return appDict

def getProgress(res):

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
    finally:
        return progress



def run(ip):
    while True:
        appDict = getAppID_Port()
        priority = []
        if len(appDict.keys()) == 0:
            print("没有Spark任务运行")
            time.sleep(2)
            continue
        print("Spark任务列表:", appDict.keys())
        for app in appDict:
            # print("Spark 任务: {}".format(app))
            res = getResponse(ip, appDict[app])
            if res is None : continue
            p = getProgress(res)
            if "progress" not in p.keys(): continue
            print("Spark任务 {0} 的工作进度为：---{1:.2f}%---".format(app, p["progress"] * 100))
            priority.append([app, p["progress"] * 100])

        priority.sort(key=lambda x: x[1], reverse=False)
        job_order = [x[0] for x in priority]
        print("Progress 动态队列:", job_order)

        time.sleep(4)


if __name__ == '__main__':
    ip = "192.168.1.106"
    run(ip)



