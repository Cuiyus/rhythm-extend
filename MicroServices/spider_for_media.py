import requests
import json ,os , sys, time
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
        
    url = "http://192.168.3.110:30913/api/traces"
    local_time = time.time() * 1000
    local_time = int(local_time) * 1000
    start_timestamp = str(local_time-3600000000).replace('.','')
    end_timestamp = str(local_time).replace('.','')

    kv = {
        # "end": "1587197268058000",
        "end": end_timestamp,
        "limit":limit,
        "lookback":"2h",
        "service":"nginx",
        "start": start_timestamp
        # "start":"1587193668058000"
    }
    header = {
        "user-agent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
        "host":'192.168.3.110:30913',
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
    data_span_27 = []
    json_data = json.loads(response.text)
    trace_num = len(json_data['data']) # trace_num -- request number with tracing
    request_span_27 = []

    
    for request_id, trace in enumerate(json_data['data']):
        if len(trace['spans']) == 27 :
            # pprint(trace['spans'][7])
            # print('--------------------------------------------------------------------------')
            request_span_27.append(request_id)
            data_span_27.append(trace)
  
    # pprint(trace_num)
    # pprint(data_span_8[0])
    print("Number of data :%d" % len(data_span_27))
    return data_span_27

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
        # '1_timestamp',
        'nginx_1 /ms',
        # '2_timestamp',
        'nginx_3 /ms',
        # 'mis-timestamp',
        'movie-id-svc',
        # 'mis-mmcget-timestamp',
        'mis-mmcset',
        # 'crs-timestamp',
        'mis-mmcget',
        'compose-review-svc-uploadmovieid',
        # 'rs-timestamp',
        'rating-svc',
        # 'rs-redis-timestamp',
        'rs-redis',
        'crs-uploadrating',
        'urs',
        'urs-mongoFind',
        'urs-mongoUpdate',
        'urs-redis',
        'rss',
        'rss-mongo',
        'mrs',
        'mrs-mongoFind',
        'mrs-mongoUpdate',
        'mrs-Redis',
        'nginx','urs','mrs',"crs"
    ]
    for i,name in enumerate(tablename):
        sheet.write(0,i,name)



    for i,req in enumerate(data):
        processes = req['processes']
        # duration = []
        n_1 ,n_3, mis, mis_mmcget, mis_mmcset = 0.0, 0.0, 0.0, 0.0, 0.0
        crs, rs, rs_redis, crs_r = 0.0, 0.0, 0.0, 0.0
        urs, urs_mongoFind, urs_mongoUpdate, urs_redis, rss, rss_mongo =  0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        mrs, mrs_mongoFind, mrs_mongoUpdate, mrs_redis = 0.0, 0.0, 0.0, 0.0
        for span in req['spans']:
            span_name = processes[span['processID']]['serviceName']
            span_operation = span['operationName']
            # print(span_name, span_operation)
            # if span_name == 'istio-ingressgateway' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
            #     g_t = span['duration'] / 1000.0  # ingressgateway duration time (total time)
                
            

            if span_name == 'nginx' and span_operation == '/wrk2-api/review/compose':
                n_1 = span['duration'] / 1000.0  # productage duration (total time)
                # duration.append(n_1)
                # start_p = span['startTime']
                # start_p = str(start_p)

            if span_name == 'nginx' and span_operation == 'ComposeReview':
                n_3 = span['duration'] / 1000.0  # 
                # duration
                # start_p_d = span['startTime']
                # start_p_d = str(start_p_d)

            if span_name == 'movie-id-service' and span_operation == 'UploadMovieId':
                mis = span['duration'] / 1000.0  # detail_time
                # start_d = span['startTime']
                # start_d = str(start_d)

            if span_name == 'movie-id-service' and span_operation == 'MmcSetMovieId':
                mis_mmcset = span['duration'] / 1000.0  # 
                # start_p_r = span['startTime']
                # start_p_r = str(start_p_r)

            if span_name == 'movie-id-service' and span_operation == 'MmcGetMovieId':
                mis_mmcget = span['duration'] / 1000.0  # review time
                # start_r = span['startTime']
                # start_r = str(start_r)


            if span_name == 'compose-review-service' and span_operation == 'UploadMovieId':
                crs = span['duration'] / 1000.0  # review_rating time

            if span_name == 'rating-service' and span_operation == 'UploadRating' :
                rs = span['duration'] / 1000.0  # rating_time
            
            if span_name == 'rating-service' and span_operation == 'RedisInsert' :
                rs_redis = span['duration'] / 1000.0  # rating_time
                
            if span_name == 'compose-review-service' and span_operation == 'UploadRating' :
                crs_r = span['duration'] / 1000.0  # rating_time
            
            if span_name == 'user-review-service' and span_operation == 'UploadUserReview' :
                urs = span['duration'] / 1000.0  # rating_time
            if span_name == 'user-review-service' and span_operation == 'MongoFindUser' :
                urs_mongoFind = span['duration'] / 1000.0  # rating_time        
            if span_name == 'user-review-service' and span_operation == 'MongoUpdate' :
                urs_mongoUpdate = span['duration'] / 1000.0  # rating_time                          
            if span_name == 'user-review-service' and span_operation == 'RedisUpdate' :
                urs_redis = span['duration'] / 1000.0  # rating_time

            if span_name == 'review-storage-service' and span_operation == 'StoreReview' :
                rss = span['duration'] / 1000.0  # rating_time
            if span_name == 'review-storage-service' and span_operation == 'MongoInsertReview' :
                rss_mongo = span['duration'] / 1000.0  # rating_time
            

            if span_name == 'movie-review-service' and span_operation == 'UploadMovieReview' :
                mrs = span['duration'] / 1000.0  # rating_time
            if span_name == 'movie-review-service' and span_operation == 'MongoFindMovie' :
                mrs_mongoFind = span['duration'] / 1000.0  # rating_time
            if span_name == 'movie-review-service' and span_operation == 'MongoUpdate.' :
                mrs_mongoUpdate = span['duration'] / 1000.0  # rating_time
            if span_name == 'movie-review-service' and span_operation == 'RedisUpdate' :
                mrs_redis = span['duration'] / 1000.0  # rating_time

        # Insert duration data
        if mis > urs and n_1 > mis and mis > mrs and crs_r > max(urs, mrs):
            sheet.write(i+1, 0, n_1)
            sheet.write(i+1, 1, n_3)
            sheet.write(i+1, 2, mis)
            sheet.write(i+1, 3, mis_mmcset)
            sheet.write(i+1, 4, mis_mmcget)
            sheet.write(i+1, 5, crs)
            sheet.write(i+1, 6, rs)
            sheet.write(i+1, 7, rs_redis)
            sheet.write(i+1, 8, crs_r)

            sheet.write(i+1, 9, urs)
            sheet.write(i+1, 10, urs_mongoFind)
            sheet.write(i+1, 11, urs_mongoUpdate)
            sheet.write(i+1, 12, urs_redis)

            sheet.write(i+1, 13, rss)
            sheet.write(i+1, 14, rss_mongo)
            sheet.write(i+1, 15, mrs)
            sheet.write(i+1, 16, mrs_mongoFind)
            sheet.write(i+1, 17, mrs_mongoUpdate)
            sheet.write(i+1, 18, mrs_redis)
            sheet.write(i+1, 19, n_1-mis)
            sheet.write(i+1, 20, urs-urs_mongoFind)
            sheet.write(i+1, 21, mrs-mrs_mongoFind)
            sheet.write(i+1, 22, crs_r - max(urs, mrs))
        else:
            continue

    book.save(path)

def isEnough(path):
    workbook = xlrd.open_workbook(path)
    table = workbook.sheets()[0]
    nrows = table.nrows
    if nrows <= 10000:
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
    
    for i,req in enumerate(data):
        processes = req['processes']
        n_1 ,n_3, mis, mis_mmcget, mis_mmcset = 0.0, 0.0, 0.0, 0.0, 0.0
        crs, rs, rs_redis, crs_r = 0.0, 0.0, 0.0, 0.0
        urs, urs_mongoFind, urs_mongoUpdate, urs_redis, rss, rss_mongo =  0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        mrs, mrs_mongoFind, mrs_mongoUpdate, mrs_redis = 0.0, 0.0, 0.0, 0.0


        # duration = []
        for span in req['spans']:
            span_name = processes[span['processID']]['serviceName']
            span_operation = span['operationName']
            # print(span_name, span_operation)
            # if span_name == 'istio-ingressgateway' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
            #     g_t = span['duration'] / 1000.0  # ingressgateway duration time (total time)
                
            

            if span_name == 'nginx' and span_operation == '/wrk2-api/review/compose':
                n_1 = span['duration'] / 1000.0  # productage duration (total time)
                # duration.append(n_1)
                # start_p = span['startTime']
                # start_p = str(start_p)

            if span_name == 'nginx' and span_operation == 'ComposeReview':
                n_3 = span['duration'] / 1000.0  # 
                # duration
                # start_p_d = span['startTime']
                # start_p_d = str(start_p_d)

            if span_name == 'movie-id-service' and span_operation == 'UploadMovieId':
                mis = span['duration'] / 1000.0  # detail_time
                # start_d = span['startTime']
                # start_d = str(start_d)

            if span_name == 'movie-id-service' and span_operation == 'MmcSetMovieId':
                mis_mmcset = span['duration'] / 1000.0  # 
                # start_p_r = span['startTime']
                # start_p_r = str(start_p_r)

            if span_name == 'movie-id-service' and span_operation == 'MmcGetMovieId':
                mis_mmcget = span['duration'] / 1000.0  # review time
                # start_r = span['startTime']
                # start_r = str(start_r)


            if span_name == 'compose-review-service' and span_operation == 'UploadMovieId':
                crs = span['duration'] / 1000.0  # review_rating time

            if span_name == 'rating-service' and span_operation == 'UploadRating' :
                rs = span['duration'] / 1000.0  # rating_time
                # print(rs)
            
            if span_name == 'rating-service' and span_operation == 'RedisInsert' :
                rs_redis = span['duration'] / 1000.0  # rating_time
                # print(rs_redis)
            if span_name == 'compose-review-service' and span_operation == 'UploadRating' :
                crs_r = span['duration'] / 1000.0  # rating_time
            
            if span_name == 'user-review-service' and span_operation == 'UploadUserReview' :
                urs = span['duration'] / 1000.0  # rating_time
            if span_name == 'user-review-service' and span_operation == 'MongoFindUser' :
                urs_mongoFind = span['duration'] / 1000.0  # rating_time        
            if span_name == 'user-review-service' and span_operation == 'MongoUpdate' :
                urs_mongoUpdate = span['duration'] / 1000.0  # rating_time                          
            if span_name == 'user-review-service' and span_operation == 'RedisUpdate' :
                urs_redis = span['duration'] / 1000.0  # rating_time

            if span_name == 'review-storage-service' and span_operation == 'StoreReview' :
                rss = span['duration'] / 1000.0  # rating_time
            if span_name == 'review-storage-service' and span_operation == 'MongoInsertReview' :
                rss_mongo = span['duration'] / 1000.0  # rating_time
            

            if span_name == 'movie-review-service' and span_operation == 'UploadMovieReview' :
                mrs = span['duration'] / 1000.0  # rating_time
            if span_name == 'movie-review-service' and span_operation == 'MongoFindMovie' :
                mrs_mongoFind = span['duration'] / 1000.0  # rating_time
            if span_name == 'movie-review-service' and span_operation == 'MongoUpdate.' :
                mrs_mongoUpdate = span['duration'] / 1000.0  # rating_time
            if span_name == 'movie-review-service' and span_operation == 'RedisUpdate' :
                mrs_redis = span['duration'] / 1000.0  # rating_time

        # Insert duration 
        # print(nrows)
        if mis > urs and n_1 > mis and mis > mrs and crs_r > max(urs, mrs):
            sheet.write(nrows+i, 0, n_1)
            sheet.write(nrows+i, 1, n_3)
            sheet.write(nrows+i, 2, mis)
            sheet.write(nrows+i, 3, mis_mmcset)
            sheet.write(nrows+i, 4, mis_mmcget)
            sheet.write(nrows+i, 5, crs)
            # print(rs, rs_redis)
            sheet.write(nrows+i, 6, rs)
            sheet.write(nrows+i, 7, rs_redis)

            
            sheet.write(nrows+i, 8, crs_r)

            sheet.write(nrows+i, 9, urs)
            sheet.write(nrows+i, 10, urs_mongoFind)
            sheet.write(nrows+i, 11, urs_mongoUpdate)
            sheet.write(nrows+i, 12, urs_redis)

            sheet.write(nrows+i, 13, rss)
            sheet.write(nrows+i, 14, rss_mongo)
            sheet.write(nrows+i, 15, mrs)
            sheet.write(nrows+i, 16, mrs_mongoFind)
            sheet.write(nrows+i, 17, mrs_mongoUpdate)
            sheet.write(nrows+i, 18, mrs_redis)
            sheet.write(nrows+i, 19, n_1-mis)
            sheet.write(nrows+i, 20, urs-urs_mongoFind)
            sheet.write(nrows+i, 21, mrs-mrs_mongoFind)
            sheet.write(nrows+i, 22, crs_r - max(urs, mrs))
        else:
            continue
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
        path = '/home/tank-cys/cuiys_data/media-micro/conf_%s_qps_%s_%d.xls' % (conf,qps,i)
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
    



