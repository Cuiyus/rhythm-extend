# 创建数据库，并创建表

import mysql.connector
import subprocess

# mysql

class initDB(object):
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.passwd = password
        self._conn, self._cur = self.createDB()

    def createDB(self):
        try:
            mydb = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.passwd
            )
            cursor = mydb.cursor()
            cursor.execute('show databases')
            rows = cursor.fetchall()
            dbname = [row[0] for row in rows]
            if "rhythm" not in dbname: cursor.execute("create database rhythm")
            cursor.execute('use rhythm')
        except Exception as err:
            print("数据库连接失败 %s" % err)
        else:
            return mydb, cursor

    def createTable(self, tablename):
        if tablename == "scimark":
            sql = '''
                        create table if not exists `scimark`(
                        `appId` int primary key AUTO_INCREMENT not null,
                        `Pid` int not null,
                        `cpuNum` int not null,
                        `timeStamp` int not null,
                        `interruptStamp` int  
                        )
                    '''
        elif tablename == "AI":
            pass
        elif tablename == "spark":
            pass

        self._cur.execute('show tables')
        rows = self._cur.fetchall()
        tablenames = [row[0] for row in rows]
        try:
            if tablename not in tablenames:
                self._cur.execute(sql)
        except Exception as err:
            print("创建表连接失败 %s" % err)

    def close(self):
        try:
            if (type(self._cur) == 'object'):
                self._cur.close()
            # if (type(self._conn) == 'object'):
            #     self._conn.close()
        except:
            raise ("关闭异常, %s,%s" % (type(self._cur), type(self._conn)))

    def insert(self, tablename, data):
        if tablename == "scimark":
            sql = "insert into scimark(Pid, cpuNum, timeStamp, interruptStamp) values (%s, %s, %s, %s)"
        elif tablename == "AI":
            pass
        elif tablename =="spark":
            pass
        try:
            # self._cur.execute(sql, [data["pid"], data["cpuNum"],data['timestamp'], data["interruptStamp"]])
            self._cur.execute(sql, [data["pid"], data["cpuNum"], data['timestamp'], data["interruptStamp"]])
            self._conn.commit()
        except Exception as err:
            self._conn.rollback()
            print("执行失败 %s" % err)

    def test(self, data):
        # sql = "insert into scimark (Pid, cpuNum, timeStamp,interruptStamp)" \
        #       "values " \
        #       "(10086, 2, 21, 10)"
        sql = "insert into scimark(Pid, cpuNum, timeStamp, interruptStamp) values (%s, %s, %s, %s)"
        self._cur.execute(sql,[data["pid"], data["cpuNum"],data['timestamp'], data["interruptStamp"]])
        self._conn.commit()

    def select(self):
        sql = "select * from scimark"
        self._cur.execute(sql)
        rows = self._cur.fetchall()
        print(rows)

if __name__ == '__main__':

    host='localhost'
    user='root'
    password='root'

    rhythm = initDB(host, user, password)
    rhythm.createTable('scimark')
    data = {'pid':10086, "cpuNum":2, "timestamp":10023, "interruptStamp":None}
    rhythm.insert("scimark", data)
    rhythm.select()



