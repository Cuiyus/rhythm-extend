from flask import Flask, jsonify, request
import subprocess
app = Flask(__name__)

@app.route("/runcnn",methods=["GET"])
def runcnn():
    port = request.args.get("port")
    step = request.args.get("step")
    cmd= "bash /root/runcnn.sh {} {}".format(port, step)
    print(cmd)
    subprocess.run(cmd, shell=True)
    return "Start cnn"
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=22222)