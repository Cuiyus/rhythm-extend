from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time, subprocess
import threading, re
import numpy as np
from scipy.optimize import curve_fit

'''
生成两个队列，可预测与不可预测
可预测：AI与Spark
不可预测：SCIMARK
'''
# SCIMARK
