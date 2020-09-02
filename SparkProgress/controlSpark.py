from spiderForSpark import  getAppID_Port
import time, requests
from bs4 import BeautifulSoup
import subprocess
'''
使用spark Rest接口获取executor信息
参考链接：
1. https://www.cnblogs.com/Swidasya/p/7482679.html
2. https://blog.csdn.net/darkWatch/article/details/84860675

'''
def getResponse(ip, app, port=18080):
    # url : "http://192.168.1.106:18080/api/v1/applications/application_1597656922163_0049/executors"
    url = "http://{0}:{1}/api/v1/applications/{2}/executors/".format(ip, port, app)
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response
    except requests.exceptions.HTTPError:
        print("{} 任务未完成初始化".format(ip))
        return None

def getCoarseGrainedExecutorPort(res):
    driver = res.json()[0]
    executor = res.json()[1:]
    executor_dict = {}
    for exe in executor:
        address, port = exe["hostPort"].split(":")
        executor_dict[address] = port
    return executor_dict

def getLocation(ip):
    appDict = getAppID_Port()
    appExe = {}
    if len(appDict.keys()) == 0:
        print("没有Spark任务运行")
        time.sleep(4)

    for app in appDict:
        res = getResponse(ip, app)
        if res is None: continue
        executor_dict = getCoarseGrainedExecutorPort(res)
        appExe[app] = executor_dict
        print("正在运行的Spark作业有:{}".format(app))
        print("运行的节点有:{}".format(executor_dict.keys()))
    return  appExe

def killExecutor(ip):
    appexe = getLocation(ip)
    try:
        # 注意每次只能kill一个任务
        #app:application_1597656922163_0049
        app = input("输入要kill的任务：")
        #add:master slave1 slave2
        add = input("输入任务{}需要kill的节点：".format(app)).split(" ")
        temp = add.copy()
        for i, d in enumerate(temp):
            if d == "master":
                temp[i] = "Spark-1"
            elif d == "slave1":
                temp[i] = "Spark-2"
            elif d=="slave2":
                temp[i] = "Spark-3"
    except:
        print("重新检查输入")
    for i,d in enumerate(add):
        cmd = ["docker", "exec", "-i", temp[i], "bash", "/root/controlJob.sh", appexe[app][d]]
        info = subprocess.run(cmd, stdout=subprocess.PIPE)
        print(info)

    print("已删除{}节点的{}任务".format(add,app))


if __name__ == '__main__':
    ip = "192.168.1.106"
    while True:
        killExecutor(ip)






























