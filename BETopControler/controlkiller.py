import subprocess, requests
import re

class SparkKiller(object):
    def __init__(self, spark, job, worker):
        self.spark = spark
        self.job = job
        self.relative = {
            "Spark-1":"master",
            "Spark-2":"slave1",
            "Spark-3":"slave2"
        }
        self.sparkcontroler = "Spark-1"
        self.worker = worker
        self.node = None
        self.setNode(worker)
        self.executorPid = None
        self.getExecutorPid()

        self.record = set()

    def setNode(self, worker):
        if self.worker not in self.relative.keys():
            print("传入worker错误，不存在名称为{}的spark Worker".format(self.worker))
        else:
            self.node = self.relative[worker]
            print("查询节点{}是否存在executor".format(self.node))

    def getExecutorPid(self):
        executor = self.spark.app_Executor[self.job[0]]
        print('1', executor, self.node)
        nodeinfo = None
        # 假设要kill的节点为spark-1
        for exec in executor:
            if self.node != exec[0]:
                continue
            else:
                nodeinfo = exec

        if nodeinfo:
            print("{}节点存在运行的executor，对正在运行的LC造成了干扰".format(self.node))
            cmd = "docker exec -i {} lsof -i:{}".format(self.worker, nodeinfo[1])
            pidfinfo = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
            info = pidfinfo.stdout.decode('utf-8').split('\n')[-2]
            executorPidPat = re.compile(r'java    (\d{3,5}) root')
            executorPid = executorPidPat.findall(info)[0]
        else:
            print("{}节点不存在运行的executor".format(self.node))
            return None
        if not executorPid:
            print("获取Exectuor pid失败")
            return None
        self.executorPid =executorPid
        return executorPid

    def killExecutor(self):
        print("kill Executor", self.worker, self.executorPid)
        cmd = "docker exec -i {} kill -9 {}".format(self.worker, self.executorPid)
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)

    def killApplication(self):
        print("kill Spark", self.job)
        cmd = "docker exec -i {} yarn application -kill {}".format(self.sparkcontroler,self.job[0])
        killinfo = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
        killInfo = killinfo.stdout.decode('utf-8').split('\n')
        print(killInfo)


class killer(object):
    def __init__(self, jobinfo, worker, app):
        self.job_info = jobinfo
        self.worker = worker
        self.app = app

        self.spark = None
        self.ai = None
        self.sci = None

    def chooseKiller(self):
        if self.job_info[2] == "spark":
            self.spark = SparkKiller(spark=self.app, worker=self.worker, job=self.job_info)
            # 查看excutoePID能否正常输出
            return self.spark.executorPid
        elif self.job_info[2] == "AI": self.aiKill()
        elif self.job_info[2] == "sci": self.scikill()

    def sparkKill(self):
        executor = self.spark.app_Executor[self.job_info[0]]
        for exec in executor:
            if exec[0] == "master":
                pass
        pass

    def aiKill(self):
        pass

    def scikill(self):
        pass



    def operating(self):
        if self.job_info[2] == "spark":
            print("kill Spark", self.job_info)
            cmd = "docker exec -i Spark-1 yarn application -kill {}".format(self.job_info[0])
            killinfo = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
            killInfo = killinfo.stdout.decode('utf-8').split('\n')
            print(killInfo)
        elif self.job_info[2] == "AI":
            print("kill AI", self.job_info)
            cmd = "bash /home/tank/cys/rhythm/BE/cnn-bench/CnnBenchProgress/scripts/killcnnJob.sh {}".format(self.job_info[0])
            killinfo = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
            killInfo = killinfo.stdout.decode('utf-8').split('\n')
            print(killInfo)
        elif self.job_info[2] == "sci":
            print("kill sci", self.job_info)
            cmd = "docker exec -i Scimark kill -9 {}".format(self.job_info[0])
            subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)

if __name__ == '__main__':
    k = killer()
    # k.job_info = ["11115",0.047367773968495654,"AI"]
    # k.job_info = ["application_1599144170737_0039", 0.06666666666666667, "spark"]
    k.job_info = ["37627", 61.509, "sci"]
    k.operating()




