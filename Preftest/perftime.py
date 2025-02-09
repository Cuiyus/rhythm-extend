from functools import wraps
import time
import configparser
def readConfig():
    cfg = configparser.ConfigParser()
    cfgname = "../config/config.ini"
    cfg.read(cfgname, encoding='utf-8')
    return cfg
def func_timer(function):
    '''
    用装饰器实现函数计时
    :param function: 需要计时的函数
    :return: None
    '''
    @wraps(function)
    def function_timer(*args, **kwargs):
        path = "./perftime.txt"
        with open(path, "a+") as f:
            print('[Function: {name} start...]'.format(name = function.__name__), file=f)
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        with open(path, "a+") as f:
            print('[Function: {name} finished, spent time: {time:.2f}s]'.format(name = function.__name__,time = t1 - t0), file=f)
        return result
    return function_timer


class MyTimer(object):
    '''
    用上下文管理器计时
    '''
    def __init__(self, testcode, loger=None):
        self.testcode = testcode
        self.cfg = readConfig()
        self.loger = loger

    def __enter__(self):
        self.t0 = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        path = self.cfg.get("Experiment", "perf")
        with open(path, "a+") as f:
            info = '[finished, {} spent time: {time:.2f}s]'.format(self.testcode, time = time.time() - self.t0)
            if self.loger: self.loger.info(info)
            print('[finished, {} spent time: {time:.2f}s]'.format(self.testcode, time = time.time() - self.t0), file=f)
