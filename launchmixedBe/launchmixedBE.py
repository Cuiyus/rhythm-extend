"""有序启动混合类型BE"""
import subprocess
from flask import Flask, jsonify, request, Response
# 用生成器来实现

def launchBE(be):
    cmd = ""
    if be == "AI":
        step = 1000
        cmd = "docker exec -i Tensor-Worker-1 bash /home/tank/addBeCopy_cnn.sh {}".format(step)
        subprocess.run(cmd, shell=True)
        return "Start AI"
    elif be == "Kmeans":
        cmd = "docker exec -i Spark-1 bash /root/spark-bench-legacy/submit_job.sh KMeans"
        subprocess.run(cmd, shell=True)
        return "Start Kmeans"
    elif be == "LogisticRegression":
        cmd = "docker exec -i Spark-1 bash /root/spark-bench-legacy/submit_job.sh LogisticRegression"
        subprocess.run(cmd, shell=True)
        return "Start LogisticRegression"
    elif be == "Hpcc":
        cmd = "docker exec -i Scimark-1 bash /home/tank/addBeCopy_cpu.sh  "
        subprocess(cmd, shell=True)
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
    BElist = ["AI", "Kmeans", "Hpcc",
              "AI", "LogisticRegression", "Hpcc",
              "AI", "Kmeans", "Hpcc", "Hpcc"]
    global loader
    loader = run(BElist)
    app.run(host="0.0.0.0", port=10081)

