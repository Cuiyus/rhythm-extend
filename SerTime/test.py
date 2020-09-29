import requests, re, time
from bs4 import BeautifulSoup
class test(object):
    def __init__(self):
        self.ip = "192.168.1.106"
        self.appProgress = []

    def catch(self):
        url = "http://{0}:{1}".format(self.ip, app[1])
        print(url)
        try:
            res = requests.get(url)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
        except requests.exceptions.HTTPError:
            print("{} 任务未完成初始化".format(app[0]))
            return None
        except requests.exceptions.ConnectionError:
            print("任务：{} --- 连接错误".format(app[0]))
            return None
        running_job, compile_job, total_job = 0, 0, 0

        soup = BeautifulSoup(res.text.encode("utf-8"), 'lxml')
        activateJobInfo = soup.find("table", attrs={'id':"activeJob-table"}).\
            select('span[style="text-align:center; position:absolute; width:100%; left:0;"]')
        completedJobInfo = soup.find("table", attrs={'id':"completedJob-table"}).\
            select('span[style="text-align:center; position:absolute; width:100%; left:0;"]')

        task_pat = re.compile(r'(\d{1,3})/(\d{1,3})')
        runningJobTaskInfo = task_pat.findall(activateJobInfo[0].string)[0]
        completedJobTaskInfo = task_pat.findall(completedJobInfo[0].string)
        for _ in completedJobTaskInfo:
            total_job += int(_[0])
        # 已运行的Job所有Task之和
        total_job += int(runningJobTaskInfo[1])
        running_job = int(runningJobTaskInfo[0])
        pro = running_job/ int(runningJobTaskInfo[1])
        print(running_job, runningJobTaskInfo[1])
        print(pro)

    def getProgress(self, app):
        # 使用了爬虫解析4040的spark页面
        '''
        :param res:
        :return:获取单个任务的工作进度
        '''
        url = "http://{0}:{1}".format(self.ip, app[1])
        print(url)
        try:
            res = requests.get(url)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
        except requests.exceptions.HTTPError:
            print("{} 任务未完成初始化".format(app[0]))
            return None
        except requests.exceptions.ConnectionError:
            print("任务：{} --- 连接错误".format(app[0]))
            return None

        soup = BeautifulSoup(res.text.encode("utf-8"), 'lxml')
        res1 = soup.select('span[style="text-align:center; position:absolute; width:100%; left:0;"]')
        progress = {}
        compilejob_info = {}
        running_job, compile_job = 0, 0
        task_pat = re.compile(r'(\d{1,3})/(\d{1,3})')
        print(res.text)
        for _ in res1:
            if "running" in str(_):
                running_job += 1
                p = task_pat.search(str(_))
                progress[running_job] = {}
                progress[running_job]["running_task"] = int(p.group(1))
                progress[running_job]["total_task"] = int(p.group(2))
            else:
                compile_job += 0
                p = task_pat.search(str(_))
                compilejob_info[compile_job] = {}
                compilejob_info[compile_job]["total_task"] = int(p.group(2))
                compilejob_info[compile_job]["progress"] = "100%"

        running_task = 0
        total_task = 0

        for task in progress.values():
            running_task += task["running_task"]
            total_task += task["total_task"]
        try:
            progress["progress"] = running_task / total_task
        except ZeroDivisionError:
            print("The spark Job提交后未完成任务初始化，Total Task= 0")
            return None

        self.appProgress.append([app[0], progress["progress"], "spark"])
        return progress
while True:
    t=test()
    app = ["application_1601370732531_0015", 4040]
    p = t.catch()
    time.sleep(0.5)
    break
