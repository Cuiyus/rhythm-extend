"""有序启动混合类型BE"""
import subprocess
from threading import Thread
import time, sys
import configparser
from copy import deepcopy
import logging, threading
sys.path.append(r"/home/tank/cys/rhythm/BE/rhythm-extend")
# 日志
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 函数性能测试
from Preftest.perftime import func_timer, MyTimer
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

        with open(self.logpath, "wb+") as f: f.truncate()


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

    def record(self, be, job, order):
        timeout = 1
        f = open(self.logpath, 'a+')
        if be == "AI":
            app_nums = self.cnncount
            logger.info("App_num {} self.cnncount {}".format(app_nums, self.cnncount))
        elif (be == "KMeans") or (be == "LogisticRegression"):
            app_nums = self.sparkcount
            logger.info("App_num {} self.count {}".format(app_nums, self.sparkcount))
        elif be == "Hpcc":
            app_nums = self.scicount
            logger.info("App_num {} self.count {}".format(app_nums, self.scicount))
        with MyTimer("获取{}任务列表".format(be)):
            appdict = job.getAppDict()
            logger.info("第0次{}信息拉取：{}".format(be, appdict))
        with MyTimer("{}更新应用信息".format(type)):
            i = 0
            while ((not appdict) or (len(appdict) != app_nums)):
                i += 1
                appdict = job.getAppDict()
                time.sleep(timeout)
        print("----------------------------------------", file=f)
        print("已启动任务的数量：{}".format(app_nums), file=f)
        print("已启动任务的列表：{}".format(app_nums), file=f)
        with MyTimer("cnn序号应用信息相匹配"):
            info = appdict - (appdict & self.appbak)
            self.activeJobInfo[order] = list(info)[0]
            self.appbak = self.appbak.union(info)
        f.close()

    def launchBE(self, be, order):
        with open(self.logpath, "a+") as f:
            print('----' * 10, file=f)
            print("Curren Launch {}th job {}".format(order, be), file=f)
        f = open(self.logpath, 'a+')
        if be == "AI":
            self.cnncount += 1
            step = self.cfg.get("AI", 'step')
            self.launchOrder[order] = "AI"
            ai = Thread(target=self.launchAi, args=(step,))
            ai.start()
            cnnrecord = Thread(target=self.record, args=(be, self.cnn, order))
            cnnrecord.start()
            return "Start AI"
        elif be == "KMeans":
            self.sparkcount += 1
            self.launchOrder[order] = "Kmeans"
            kmeans = Thread(target=self.launchSpark, args=(be,))
            kmeans.start()
            kmeansrecord = Thread(target=self.record, args=(be, self.spark, order))
            kmeansrecord.start()
            return "Start KMeans"
        elif be == "LogisticRegression":
            self.sparkcount += 1
            self.launchOrder[order] = "LogisticRegression"
            lg = Thread(target=self.launchSpark, args=("LogisticRegression",))
            lg.start()
            lgrecord = Thread(target=self.record, args=(be, self.spark, order))
            lgrecord.start()
            return "Start LogisticRegression"
        elif be == "Hpcc":
            self.scicount += 1
            self.launchOrder[order] = "hpcc"
            hpcc = Thread(target=self.launchHpcc)
            hpcc.start()
            hpccrecord = Thread(target=self.record, args=(be, self.sci, order))
            hpccrecord.start()
            return "Start Hpcc"
        f.close()

    def launchAi(self, step):
        cmd = "docker exec -i Tensor-Worker-1 bash /home/tank/addBeCopy_cnn.sh {}".format(step)
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    def launchSpark(self, be):
        cmd = "docker exec -i Spark-1 bash /root/spark-bench-legacy/bin/submit_job.sh {}".format(be)
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    def launchHpcc(self):
        cmd = "docker exec -i Scimark bash /home/tank/addBeCopy_cpu.sh  "
        subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

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
        subprocess.run(cmd1, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        subprocess.run(cmd2, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        subprocess.run(cmd3, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        self.scicount, self.sparkcount, self.cnncount = 0, 0, 0