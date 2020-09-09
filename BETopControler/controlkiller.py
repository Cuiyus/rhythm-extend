import subprocess
class killer(object):
    def __init__(self):
        self.job_info = None

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




