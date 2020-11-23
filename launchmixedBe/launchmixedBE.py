"""有序启动混合类型BE"""
import subprocess
from flask import Flask, jsonify, request, Response
from threading import Thread
# 用生成器来实现

def launchAi(step):
    cmd = "docker exec -i Tensor-Worker-1 bash /home/tank/addBeCopy_cnn.sh {}".format(step)
    subprocess.run(cmd, shell=True)

def launchSpark(be):
    cmd = "docker exec -i Spark-1 bash /root/spark-bench-legacy/bin/submit_job.sh {}".format(be)
    subprocess.run(cmd, shell=True)

def launchHpcc():
    cmd = "docker exec -i Scimark bash /home/tank/addBeCopy_cpu.sh  "
    subprocess.run(cmd, shell=True)


def launchBE(be):
    if be == "AI":
        step = 1000
        ai = Thread(target=launchAi, args=(step,))
        ai.start()
        return "Start AI"
    elif be == "KMeans":
        kmeans = Thread(target=launchSpark, args=(be,))
        kmeans.start()
        return "Start KMeans"
    elif be == "LogisticRegression":
        lg = Thread(target=launchSpark, args=("LogisticRegression",))
        lg.start()
        return "Start LogisticRegression"
    elif be == "Hpcc":
        hpcc = Thread(target=launchHpcc)
        hpcc.start()
        return "Start Hpcc"

def run(joblist):
    for i, be in enumerate(joblist):
        print(i)
        yield launchBE(be)

app = Flask(__name__)
@app.route("/launchmix", methods=["GET",])
def launchmix():
    try:
        return next(loader)
    except StopIteration:
        return "没有后续任务待启动"

if __name__ == '__main__':
    BElist = ["AI", "KMeans", "Hpcc",
              "AI", "LogisticRegression", "Hpcc",
              "AI", "KMeans", "Hpcc", "Hpcc"]
    global loader
    loader = run(BElist)
    app.run(host="0.0.0.0", port=10081)

