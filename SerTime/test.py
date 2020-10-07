import requests
class test(object):
    def __init__(self):
        self.ip = "192.168.1.106"
        self.restport=18080
    def exe(self, app):
        url = "http://{0}:{1}/api/v1/applications/{2}/executors/".format(self.ip, self.restport, app)
        executorDict = []
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except requests.exceptions.HTTPError:
            print("{} 任务未完成初始化 -- getAppCoarseGrainedExecutorPort".format(app))
            return None

t = test()
t.exe("application_1602044812944_0007")