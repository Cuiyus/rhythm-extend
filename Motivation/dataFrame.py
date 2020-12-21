# 构建队列以满足队首出队的要求
class queue(list):
    def __init__(self):
        super().__init__()
        self.stack1 = []
        self.stack2 = []
    def push(self, x):
        self.stack1.append(x)

    def pop(self):
        if not self.stack2:
            while self.stack1:
                tmp = self.stack1.pop()
                self.stack2.append(tmp)
        res = self.stack2.pop()
        return res

    def peek(self):
        if not self.stack2:
            while self.stack1:
                tmp = self.stack1.pop()
                self.stack2.append(tmp)
        res = self.stack2[-1]
        return res

    def empty(self):
        if not self.stack2:
            while self.stack1:
                tmp = self.stack1.pop()
                self.stack1.append(tmp)
        self.stack2.clear()

    def sort(self):
        super().sort()


