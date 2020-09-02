import subprocess,sys
def appisAlive(pid):
    cmd = "docker exec -i Scimark ps aux | grep {}".format(pid)
    info = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True)
    if info:
        return True
    else:
        return False
pid = sys.argv[1]
if appisAlive(pid): print(pid,"Running")
else:print(pid,"NotRunning")
