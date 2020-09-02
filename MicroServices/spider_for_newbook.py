import requests
import json ,os , sys
import xlwt,xlrd
from pprint import pprint
import pandas as pd
import time
from xlutils.copy import copy
def default_process():
    if (len(sys.argv) == 2):
        filename = sys.argv[1]

    if os.path.exists(filename):
        raise('Enter a new excel name')

    return filename
def buildreq(limit):
    '''
    build request 
    return url, params, header
    '''
        
    url = "http://192.168.3.110:30834/api/traces"
    local_time = time.time() * 1000
    local_time = int(local_time) * 1000
    start_timestamp = str(local_time-3600000000).replace('.','')
    end_timestamp = str(local_time).replace('.','')

    kv = {
        # "end": "1587197268058000",
        "end": end_timestamp,
        "limit":limit,
        "lookback":"2h",
        "service":"details.default",
        "start": start_timestamp
        # "start":"1587193668058000"
    }
    header = {
        "user-agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
        "host":'192.168.3.110:30834',
        "Connection": "keep-alive"
    }
    return url, kv ,header

def Getresponse(limit):
    url, kv, header = buildreq(limit)
    try:
        print(1)
        response = requests.get(url, params=kv,headers=header)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        print(2)
        return response
    except:
        raise requests.HTTPError
def read_json(path):
    with open(path,'r') as j:
        load_data = json.load(j)
        return load_data
def filtertrace(response):
    '''
    filter span ==8
    return data with span=8
    '''
    data_span_5 = []
    json_data = json.loads(response.text)
    trace_num = len(json_data['data']) # trace_num -- request number with tracing
    request_span_5 = []

    
    for request_id, trace in enumerate(json_data['data']):
        if len(trace['spans']) == 6 or len(trace['spans']) == 5 :
            # pprint(trace['spans'][7])
            # print('--------------------------------------------------------------------------')
            request_span_5.append(request_id)
            data_span_5.append(trace)
  
    # pprint(trace_num)
    # pprint(data_span_8[0])
    print("Number of data :%d" % len(data_span_5))
    return data_span_5

def parserdata(data,path):
    '''
    Parser data which contains the time for spans(8)
    return: excel
        ingressgateway duration time (total time)
            productage duration (total time)
                productage_detail duration time
                    detail duration time
                productage_review time
                    review time
                        review-ratings time
                            rating time
        
    '''
    # Create table
    book = xlwt.Workbook()
    sheet = book.add_sheet(u'sheet1', cell_overwrite_ok=True)
    # Insert table name
    tablename = [
        'start_p(timestamp)',
        'productage(total time) /ms',
        'start_p_d(timestamp)',
        'productage_detail /ms',
        'start_d(timestamp)',
        'detail /ms',
        'start_p_r(timestamp)',
        'productage_review /ms',
        'start_r(timestamp)',
        'review /ms',
    ]
    for i,name in enumerate(tablename):
        sheet.write(0,i,name)



    for i,req in enumerate(data):
        processes = req['processes']
        start_p, start_p_d, start_d = '', '', ''
        start_p_r, start_r = '', ''
        p_d_t, p_d_tt, d_t = 0.0, 0.0, 0.0
        p_r_t, r_t = 0.0, 0.0
        for span in req['spans']:
            span_name = processes[span['processID']]['serviceName']
            span_operation = span['operationName']
            # print(span_name, span_operation)
            # if span_name == 'istio-ingressgateway' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
            #     g_t = span['duration'] / 1000.0  # ingressgateway duration time (total time)
                
            

            if span_name == 'productpage.default' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
                p_d_tt = span['duration'] / 1000.0  # productage duration (total time)
                start_p = span['startTime']
                # start_p = str(start_p)

            if span_name == 'productpage.default' and span_operation == 'details.default.svc.cluster.local:9080/*':
                p_d_t = span['duration'] / 1000.0  # productage_detail_time
                start_p_d = span['startTime']
                # start_p_d = str(start_p_d)

            if span_name == 'details.default' and span_operation == 'details.default.svc.cluster.local:9080/*':
                d_t = span['duration'] / 1000.0  # detail_time
                start_d = span['startTime']
                # start_d = str(start_d)


            

            if span_name == 'productpage.default' and span_operation == 'reviews.default.svc.cluster.local:9080/*':
                p_r_t = span['duration'] / 1000.0  # 
                start_p_r = span['startTime']
                # start_p_r = str(start_p_r)

            if span_name == 'reviews.default' and span_operation == 'reviews.default.svc.cluster.local:9080/*':
                r_t = span['duration'] / 1000.0  # review time
                start_r = span['startTime']
                # start_r = str(start_r)


            # if span_name == 'reviews.default' and span_operation == 'ratings.default.svc.cluster.local:9080/*':
            #     r_t_t = span['duration'] / 1000.0  # review_rating time

            # if span_name == 'ratings.default' and span_operation == 'ratings.default.svc.cluster.local:9080/*' :
            #     ra_t = span['duration'] / 1000.0  # rating_time

        # Insert duration data
        if p_d_tt and p_d_t and d_t and p_r_t and r_t:
            sheet.write(i+1, 0, start_p)
            sheet.write(i+1, 1, p_d_tt)
            sheet.write(i+1, 2, start_p_d)
            sheet.write(i+1, 3, p_d_t)
            sheet.write(i+1, 4, start_d)
            sheet.write(i+1, 5, d_t)
            sheet.write(i+1, 6, start_p_r)
            sheet.write(i+1, 7, p_r_t)
            sheet.write(i+1, 8, start_r)
            sheet.write(i+1, 9, r_t)


    book.save(path)

def isEnough(path):
    workbook = xlrd.open_workbook(path)
    table = workbook.sheets()[0]
    nrows = table.nrows
    if nrows <= 5000:
        return False
    else:
        return True

def excel_append(data, path):
    workbook = xlrd.open_workbook(path, formatting_info=True)
    old_sheet= workbook.sheets()[0]
    nrows = old_sheet.nrows
    
    # print(data)
    # pprint(data)
    
    new_workbook = copy(workbook)
    sheet = new_workbook.get_sheet(0)
    i = 0
    for n,req in enumerate(data):
        processes = req['processes']
        start_p, start_p_d, start_d = '', '', ''
        start_p_r, start_r = '', ''
        p_d_t, p_d_tt, d_t = 0.0, 0.0, 0.0
        p_r_t, r_t = 0.0, 0.0
        for span in req['spans']:
            span_name = processes[span['processID']]['serviceName']
            span_operation = span['operationName']
            # print(span_name, span_operation)
            # if span_name == 'istio-ingressgateway' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
            #     g_t = span['duration'] / 1000.0  # ingressgateway duration time (total time)
                
            

            if span_name == 'productpage.default' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
                p_d_tt = span['duration'] / 1000.0  # productage duration (total time)
                start_p = span['startTime']
                start_p = str(start_p)

            if span_name == 'productpage.default' and span_operation == 'details.default.svc.cluster.local:9080/*':
                p_d_t = span['duration'] / 1000.0  # productage_detail_time
                start_p_d = span['startTime']
                start_p_d = str(start_p_d)

            if span_name == 'details.default' and span_operation == 'details.default.svc.cluster.local:9080/*':
                d_t = span['duration'] / 1000.0  # detail_time
                start_d = span['startTime']
                start_d = str(start_d)


            

            if span_name == 'productpage.default' and span_operation == 'reviews.default.svc.cluster.local:9080/*':
                p_r_t = span['duration'] / 1000.0  # 
                start_p_r = span['startTime']
                start_p_r = str(start_p_r)

            if span_name == 'reviews.default' and span_operation == 'reviews.default.svc.cluster.local:9080/*':
                r_t = span['duration'] / 1000.0  # review time
                start_r = span['startTime']
                start_r = str(start_r)


            # if span_name == 'reviews.default' and span_operation == 'ratings.default.svc.cluster.local:9080/*':
            #     r_t_t = span['duration'] / 1000.0  # review_rating time

            # if span_name == 'ratings.default' and span_operation == 'ratings.default.svc.cluster.local:9080/*' :
            #     ra_t = span['duration'] / 1000.0  # rating_time

        # Insert duration data
        if p_d_tt and p_d_t and d_t and p_r_t and r_t:
            sheet.write(nrows+i, 0, start_p)
            sheet.write(nrows+i, 1, p_d_tt)
            sheet.write(nrows+i, 2, start_p_d)
            sheet.write(nrows+i, 3, p_d_t)
            sheet.write(nrows+i, 4, start_d)
            sheet.write(nrows+i, 5, d_t)
            sheet.write(nrows+i, 6, start_p_r)
            sheet.write(nrows+i, 7, p_r_t)
            sheet.write(nrows+i, 8, start_r)
            sheet.write(nrows+i, 9, r_t)
            i = i + 1

    new_workbook.save(path)
    return nrows



def write_execl(path, json_data):
    book = xlwt.Workbook()
    sheet = book.add_sheet(u'sheet1', cell_overwrite_ok=True)
    tablename = [
        'Trace-ID', 'Num-span', 
        'span-0', 'operation-name','Duration(ms)', 
        'span-1', 'operation-name','Duration(ms)',
        'span-2', 'operation-name','Duration(ms)',
        'span-3', 'operation-name','Duration(ms)',
        'span-4', 'operation-name','Duration(ms)',
        'span-5', 'operation-name','Duration(ms)',
        'span-6', 'operation-name','Duration(ms)',]
    book = xlwt.Workbook()
    sheet = book.add_sheet(u'sheet1', cell_overwrite_ok=True)
    # print(type(data['data']))
    # len(data['data']) is num for qingqiu 
    for i,name in enumerate(tablename):
        # print(i,name)
        sheet.write(0,i,name)
    for i,q in enumerate(json_data['data']):
        # q is dict 
        # dict_keys(['traceID', 'spans', 'processes', 'warnings'])
        trace_id = q['traceID']
        # q['spans'] is list
        # print(type(q['processes']['p1']))
        Num_span = len(q['spans']) 
        sheet.write(i+1,0,trace_id)
        sheet.write(i+1,1,Num_span)
        for j,span in enumerate(q['spans']):
            # pprint.pprint(span)
            name_span = q['processes'][span['processID']]['serviceName']
            sheet.write(i+1,2+j*3, name_span)
            name_operation = span['operationName']
            sheet.write(i+1,3+j*3, name_operation)
            duration_span = span['duration']
            duration_span = duration_span/1000
            sheet.write(i+1,4+j*3,duration_span)
    
    book.save(path)

    return
    


if __name__ == "__main__":
    # filename = default_process()

    limit = 1500
    # path = '/home/tank-cys/cuiys_data/media-micro/conf_9_qps_500_3.xls'
    try:
        conf = sys.argv[1]
        qps = sys.argv[2]
    except:
        raise "QPS is Null"
    
    for i in range(1,4):
        switch = True
        path = '/home/tank-cys/cuiys_data/new_bookinfo/conf_%s_qps_%s_%d.xls' % (conf,qps,i)
        #path = "./conf_%s_qps_%s_%d.xls' % (conf,qps,i)"
        print(path)
        # break        
        while switch: 
            r = Getresponse(limit)
            print("URL: %s" % r.url)
            data_span = filtertrace(r)
            
            if os.path.exists(path):
                if isEnough(path):
                    print("The data is enough\n Location :%s" % path)
                    switch = False
                
                else:
                    print('Start Append')
                    print(excel_append(data_span, path))
                    time.sleep(3)
            else: 
                parserdata(data_span,path)  
    # parserdata(data_span,'./data/data_span8/2.xls')
   
    # data = json.loads(r.text)
    # print(data)
    # data = read_json('./traces.json')0
    # write_execl(filename, data)  
    



