import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
def optimusFunc(step, a, b, c):
    return np.power(a * step + b, -1) + c

def getStepLoss(func, data_path):
    step_loss = []
    with open(data_path, 'r') as f:
        line = f.readline()
        while line:
            line = line.strip('\n')
            step_loss.append(line.split("\t"))
            line = f.readline()
    x = [int(d[0]) for d in step_loss]
    y = [float(d[1]) for d in step_loss]
    if len(x) == 0 and len(y) == 0:
        return None
    return x,y


def stepPredict(func, data_path, loss, num=None):
    '''
    :param func: Optimus精度计算公式
    :param data_path: Cnn-bench训练任务的stop与loss
    :param loss: 指定精度
    :return: 精度计算公式中的a,b,c
    '''
    x, y = getStepLoss(func,  data_path)
    popt, pcov = curve_fit(func, x[:num], y[:num], bounds=(0, [3., 1., 0.19]))
    # popt, pcov = curve_fit(func, x[1000], y, bounds=(0, [3., 1., 0.19]))
    a, b, c = popt[0], popt[1], popt[2]
    totalStep =  1/((loss - c) * a) - (b/a)
    progress = x[-1] / totalStep
    predict = {"totalStep":totalStep, "endStep": x[-1], "progress":progress}
    data = {"step":x, "loss":y, "popt":popt, "endstep":x[-1],"endloss":y[-1], }
    return predict, data

def plot(step, loss, popt, trainingnum):
    step = np.array(step)
    loss = np.array(loss)
    loss = loss.astype(np.float64)
    plt.plot(step, loss,'yo', label='data')
    plt.plot(step, optimusFunc(step, *popt), 'k--',
             label='fit: a=%5.6f, b=%5.6f, c=%5.6f' % tuple(popt))
    # plt.plot([0.3] * 12000, 'r--')
    plt.title("Exponential Function Fitting Trainning Num-{}".format(trainingnum))
    plt.xlabel('x coordinate')
    plt.ylabel('y coordinate')
    plt.rcParams['figure.figsize'] = (30.0, 4.0)  # 设置图片尺寸
    plt.legend()
    leg = plt.legend()  # remove the frame of Legend, personal choice
    leg.get_frame().set_linewidth(0.0)  # remove the frame of Legend, personal choice
    plt.show()


def error(step, popt):
    # step = np.array(step)
    a, b, c = popt[0], popt[1], popt[2]
    l = 1/(a*step +b) + c
    return l



if __name__ == '__main__':
    path = r'cnn_appinfo/resnet110.txt'
    error1 = []
    num = 700
    step, loss = getStepLoss(optimusFunc, path)
    for num in range(10,1990,10):
        # l = float(loss[num])
        l = 0.3
        predict, data = stepPredict(optimusFunc, path, l, num)
        error1.append([predict['totalStep'], num*10])

    # print(error)

    x = [i for i in range(0, len(error1))]
    y1 = [d[0] for d in error1] # 预测总步数
    y2 = [d[1] for d in error1] # 实际步数
    # y3 = [d[1] - d[0] for d in error1]
    # print(len(x), len(y1))
    error2 = []

    data1 = []
    for num in range(10,1990,10):
        l = float(loss[num])
        # l = 0.4
        predict, data = stepPredict(optimusFunc, path, l, num)
        error2.append([predict['totalStep'], num*10])
        data1.append(data)

    y3 = [d[1] - d[0] for d in error2]
    error3 = []
    for d in data1:
        l1 = error(d["endstep"],d["popt"])
        # print(l1)
        e = l1 - d["endloss"]
        error3.append(e)

    # print(error3)
    # plt.plot(y2,error3,'k--')

    # plt.plot(y2, y3, "+-", label="Error")



    plt.plot(y2, y1, "x-", label="Predict")
    # plt.plot(x, y2, "+-", label="Fact")

    # plt.plot(x, [0] * len(x), label="Error")
    plt.show()


    predict1, data1 = stepPredict(optimusFunc, path, 0.22, num)

    plot(data["step"][:num], data["loss"][:num], data["popt"], num)

    # print(predict['totalStep'], num)