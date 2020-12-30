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

class launcher(object):
    def __init__(self, sci, spark, cnn):
        self.sci = sci
        self.spark = spark
        self.cnn = cnn
        self.scicount = self.sparkcount = self.cnncount = 0
        self.cfg = readConfig()

        self.arriveBe = list(map(lambda x: x.strip(), self.cfg.get("Experiment", "arriveBe").split(",")))
        self.arriveBetmp = deepcopy(self.arriveBe)
        self.rescheduBe = []
        self.logpath = self.cfg.get("Experiment", "log")
        self.exptype = self.cfg.get("Experiment", "type")

        self.loader = self.load()
        self.launchOrder = {}
        self.activeJobInfo = {}
        self.appbak = set()


    def load(self):
        if self.exptype == "loop":
            i = 0
            while True:
                if i == len(self.arriveBe): i = 0
                yield self.launchBE(self.arriveBe[i])
                i = i + 1
                while self.rescheduBe: yield self.launchBE(self.rescheduBe.pop(0))

        elif self.exptype == "fix":
            order = 0
            while self.arriveBe:
                job = self.arriveBe.pop(0)
                yield self.launchBE(job, order)
                order += 1
            order = 0
            while self.rescheduBe:
                job = self.rescheduBe.pop(0)
                yield self.launchBE(job, order)
                order += 1

    def reload(self):
        self.loader = self.load()

    def launchBE(self, be, order):
        timeout = 1
        with open(self.logpath, "a+") as f:
            print('----' * 10, file=f)
            print("Curren Launch {}th job {}\n".format(order, be), file=f)
        f = open(self.logpath, 'a+')
        if be == "AI":
            self.cnncount += 1
            step = self.cfg.get("AI", 'step')
            self.launchOrder[order] = "AI"
            ai = Thread(target=self.launchAi, args=(step,))
            ai.start()
            cnnappdict = self.cnn.getAppDict()
            while ((not cnnappdict) or (len(cnnappdict) != self.cnncount)):
                cnnappdict = self.cnn.getAppDict()
                time.sleep(timeout)
            print("----------------------------------------", file=f)
            print(self.cnncount, file=f)
            print(cnnappdict, file=f)
            print("-----------------------------------------", file=f)
            info = cnnappdict - (cnnappdict & self.appbak)
            self.activeJobInfo[order] = list(info)[0]
            self.appbak = self.appbak.union(info)
            return "Start AI"
        elif be == "KMeans":
            self.sparkcount += 1
            self.launchOrder[order] = "Kmeans"
            kmeans = Thread(target=self.launchSpark(), args=(be,))
            kmeans.start()
            sparkappdict = self.spark.getAppDict()
            while ((not sparkappdict) or (len(sparkappdict) != self.sparkcount)):
                sparkappdict = self.spark.getAppDict()
                time.sleep(timeout)
            print("----------------------------------------", file=f)
            print(self.sparkcount, file=f)
            print(sparkappdict, file=f)
            print("-----------------------------------------", file=f)
            info = sparkappdict - (sparkappdict & self.appbak)
            self.activeJobInfo[order] = list(info)[0]
            self.appbak = self.appbak.union(info)
            return "Start KMeans"
        elif be == "LogisticRegression":
            self.sparkcount += 1
            self.launchOrder[order] = "LogisticRegression"
            lg = Thread(target=self.launchSpark, args=("LogisticRegression",))
            lg.start()
            sparkappdict = self.spark.getAppDict()
            while ((not sparkappdict) or (len(sparkappdict) != self.sparkcount)):
                sparkappdict = self.spark.getAppDict()
                time.sleep(1)
            print("----------------------------------------", file=f)
            print(self.sparkcount, file=f)
            print(sparkappdict, file=f)
            print("-----------------------------------------", file=f)
            info = sparkappdict - (sparkappdict & self.appbak)
            self.activeJobInfo[order] = list(info)[0]
            self.appbak = self.appbak.union(info)
            return "Start LogisticRegression"
        elif be == "Hpcc":
            self.scicount += 1
            self.launchOrder[order] = "hpcc"
            hpcc = Thread(target=self.launchHpcc)
            hpcc.start()
            time.sleep(timeout)
            sciappdict = self.sci.getAppDict()
            while ((not sciappdict) or (len(sciappdict) != self.scicount)):
                sciappdict = self.sci.getAppDict()
                time.sleep(1)
            print("----------------------------------------", file=f)
            print(self.scicount, file=f)
            print(sciappdict, file=f)
            print("-----------------------------------------", file=f)
            info = sciappdict - (sciappdict & self.appbak)
            self.activeJobInfo[order] = list(info)[0]
            self.appbak = self.appbak.union(info)
            return "Start Hpcc"
        f.close()

    def launchAi(self, step):
        cmd = "docker exec -i Tensor-Worker-1 bash /home/tank/addBeCopy_cnn.sh {}".format(step)
        subprocess.run(cmd, shell=True)

    def launchSpark(self, be):
        cmd = "docker exec -i Spark-1 bash /root/spark-bench-legacy/bin/submit_job.sh {}".format(be)
        subprocess.run(cmd, shell=True)

    def launchHpcc(self):
        cmd = "docker exec -i Scimark bash /home/tank/addBeCopy_cpu.sh  "
        subprocess.run(cmd, shell=True)

    def refreshActiveJob(self):
        sciapp = list(self.sci.getAppDict())
        sparkapp = list(self.spark.getAppDict())
        cnnapp = list(self.cnn.getAppDict())
        app = sciapp + sparkapp + cnnapp
        activeOrder = []
        for i in app:
            if i in self.activeJobInfo.values():
                order = list(self.activeJobInfo.keys())[list(self.activeJobInfo.values()).index(i)]
                activeOrder.append(order)
        activeOrder.sort()
        return activeOrder

    def killBE(self):
        '''
        kill all BE
        :return:
        '''
        orders = self.refreshActiveJob()
        if orders:
            app = "--".join([self.arriveBetmp[i] for i in orders])
            self.rescheduBe = [self.arriveBetmp[i] for i in orders]
            form = "Current activeJob's(ReschdeuBe) Order: {}  App:{}\n"
            with open(self.logpath, "a+") as f:
                print("----" * 10, file=f)
                f.write(form.format(str(orders), app))
        self.activeJobInfo.clear()
        cmd1 = "docker exec -i Tensor-Worker-1 bash /home/tank/killAll.sh "
        cmd2 = "docker exec -i Spark-1 bash /home/tank/killAll.sh"
        cmd3 = "docker exec -i Scimark bash /home/tank/killAll.sh"
        subprocess.run(cmd1, shell=True)
        subprocess.run(cmd2, shell=True)
        subprocess.run(cmd3, shell=True)
        self.scicount, self.sparkcount, self.cnncount = 0, 0, 0