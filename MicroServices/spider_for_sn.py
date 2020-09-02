import requests
import json, os, sys, time
import xlwt, xlrd
from pprint import pprint
import pandas as pd
import time
from xlutils.copy import copy


def default_process():
    if (len(sys.argv) == 2):
        filename = sys.argv[1]

    if os.path.exists(filename):
        raise ('Enter a new excel name')

    return filename


def buildreq(limit):
    '''
    build request
    return url, params, header
    '''

    url = "http://192.168.1.105:30357/api/traces"
    local_time = time.time() * 1000
    local_time = int(local_time) * 1000
    start_timestamp = str(local_time - 3600000000).replace('.', '')
    end_timestamp = str(local_time).replace('.', '')

    kv = {
        # "end": "1587197268058000",
        "end": end_timestamp,
        "limit": limit,
        "lookback": "2h",
        "service": "nginx-web-server",
        "start": start_timestamp
        # "start":"1587193668058000"
    }
    header = {
        "user-agent": "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
        "host": '192.168.1.105:30357',
        "Connection": "keep-alive"
    }
    return url, kv, header


def Getresponse(limit):
    url, kv, header = buildreq(limit)
    try:
        print(1)
        response = requests.get(url, params=kv, headers=header)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        print(2)
        return response
    except:
        raise requests.HTTPError


def read_json(path):
    with open(path, 'r') as j:
        load_data = json.load(j)
        return load_data


def filtertrace(response):
    '''
    filter span ==8
    return data with span=8
    '''
    data_span_32 = []
    json_data = json.loads(response.text)
    trace_num = len(json_data['data'])  # trace_num -- request number with tracing
    request_span_32 = []

    for request_id, trace in enumerate(json_data['data']):
        if len(trace['spans']) == 27:
            # pprint(trace['spans'][7])
            # print('--------------------------------------------------------------------------')
            request_span_32.append(request_id)
            data_span_32.append(trace)

    # pprint(trace_num)
    # pprint(data_span_8[0])
    print("Number of data :%d" % len(data_span_32))
    return data_span_32


def parserdata(data, path):
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
        'nginx_1 /ms',
        'nginx_2 /ms',
        'media-service',
        'compose-post-service-uploadMedia',
        'compose-post-service-Redis',
        'user-service',
        'compose-post-service-uploadCreator',
        'compose-post-service-Redis',

        'text-service',
        'url-shorten-service',
        'compose-post-service-uploadUrls',
        'compose-post-service-Redis',
        'user-mention-service',
        'compose-post-service-uploadUserMentions',
        'compose-post-service-Redis',

        'compose-post-service-uploadText',
        'compose-post-service-Redis',
        'post-storage-service',
        'post-storage-service-Mongodb',
        'user-timeline-service',
        'user-timeline-service-mongofind',
        'user-timeline-service-mongoinsert',
        'user-timeline-service-redis',
        'write-home-timeline-service',
        'social-graph-service',
        'social-graph-service-redis',
        'social-graph-service-mongo',
        'write-home-timeline-service-redis',
        'unique-id-service',
        # 'unique-id-service-mongofind',
        'compose-post-service-uploadqueid',
        'compose-post-service-Redis',
    ]
    for i, name in enumerate(tablename):
        sheet.write(0, i, name)

    for i, req in enumerate(data):
        processes = req['processes']
        # duration = []
        n_1, n_2, media_s, composepost_media_s, composepost_media_redis, text_s = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        user_s, composepost_user_s, urlshorten_s, composepost_url_s, composepost_user_redis = 0.0, 0.0, 0.0, 0.0, 0.0
        composepost_url_redis, composepost_s, composepost_s_redis, poststorage_s,poststorage_s_mongo, usertime_s = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        usertime_s_mongoF, usertime_s_mongoI, usertime_s_redis, composepost_url_s,composepost_url_redis = 0.0, 0.0, 0.0, 0.0, 0.0
        write_home_redis, write_home_s, socialgraph_s, socialgraph_redis, socialgraph_mongo = 0.0, 0.0, 0.0, 0.0, 0.0
        usermention_s, composepost_usermention_s,composepost_usermention_redis = 0.0,0.0,0.0
        unique_s, composepost_unique_s, composepost_unique_redis = 0.0, 0.0, 0.0
        media_s_timestamp, text_s_timestamp,urlshorten_s_timestamp, composepost_s_timestamp = 0,0,0,0
        # print(type(req['spans']))
        redis_set_data={}
        for span in req['spans']:
            span_name = processes[span['processID']]['serviceName']
            span_operation = span['operationName']
            # print(span_name, span_operation)
            # if span_name == 'istio-ingressgateway' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
            #     g_t = span['duration'] / 1000.0  # ingressgateway duration time (total time)
            if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
                composepost_media_redis = span['duration'] / 1000.0  # review time
                redis_set_data[span['startTime']] = composepost_media_redis



            if span_name == 'nginx-web-server' and span_operation == '/wrk2-api/post/compose':
                n_1 = span['duration'] / 1000.0  # productage duration (total time)


            if span_name == 'nginx-web-server' and span_operation == 'ComposePost':
                n_2 = span['duration'] / 1000.0  #


            if span_name == 'media-service' and span_operation == 'UploadMedia':
                media_s = span['duration'] / 1000.0  # detail_time
                media_s_timestamp = span['startTime']

            if span_name == 'compose-post-service' and span_operation == 'UploadMedia':
                composepost_media_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_media_redis = span['duration'] / 1000.0  # review time



            if span_name == 'user-service' and span_operation == 'UploadUserWithUserId':
                user_s = span['duration'] / 1000.0  # review_rating time
            if span_name == 'compose-post-service' and span_operation == 'UploadCreator':
                composepost_user_s = span['duration'] / 1000.0  # rating_time
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_user_redis = span['duration'] / 1000.0  # review time

            if span_name == 'text-service' and span_operation == 'UploadText':
                text_s = span['duration'] / 1000.0  # review time
                text_s_timestamp: int = span['startTime']
            if span_name == 'url-shorten-service' and span_operation == 'UploadUrls':
                urlshorten_s = span['duration'] / 1000.0  # rating_time
                urlshorten_s_timestamp: int = span['startTime']
            if span_name == 'compose-post-service' and span_operation == 'UploadUrls':
                composepost_url_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_url_redis = span['duration'] / 1000.0  # review time
            if span_name == 'user-mention-service' and span_operation == 'UploadUserMentions':
                usermention_s = span['duration'] / 1000.0  # rating_time
            if span_name == 'compose-post-service' and span_operation == 'UploadUserMentions':
                composepost_usermention_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_usermention_redis = span['duration'] / 1000.0  # review time
            if span_name == 'compose-post-service' and span_operation == 'UploadText':
                composepost_s = span['duration'] / 1000.0  #
                composepost_s_timestamp: int = span['startTime']
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_s_redis = span['duration'] / 1000.0  # review time
            if span_name == 'post-storage-service' and span_operation == 'StorePost':
                poststorage_s = span['duration'] / 1000.0  # review time
            if span_name == 'post-storage-service' and span_operation == 'MongoInsertPost':
                poststorage_s_mongo = span['duration'] / 1000.0  # review time

            if span_name == 'user-timeline-service' and span_operation == 'WriteUserTimeline':
                usertime_s = span['duration'] / 1000.0  # review time
            if span_name == 'user-timeline-service' and span_operation == 'MongoFindUser':
                usertime_s_mongoF = span['duration'] / 1000.0  # review time
            if span_name == 'user-timeline-service' and span_operation == 'MongoInsert':
                usertime_s_mongoI = span['duration'] / 1000.0  # review time
            if span_name == 'user-timeline-service' and span_operation == 'RedisUpdate':
                usertime_s_redis = span['duration'] / 1000.0  # review time

            if span_name == 'write-home-timeline-service' and span_operation == 'FanoutHomeTimelines':
                write_home_s = span['duration'] / 1000.0  # review time
            if span_name == 'social-graph-service' and span_operation == 'GetFollowers':
                socialgraph_s = span['duration'] / 1000.0  # review time
            if span_name == 'social-graph-service' and span_operation == 'RedisGet':
                socialgraph_redis = span['duration'] / 1000.0  # review time
            if span_name == 'social-graph-service' and span_operation == 'MongoFindUser':
                socialgraph_mongo = span['duration'] / 1000.0  # review time
            if span_name == 'write-home-timeline-service' and span_operation == 'RedisUpdate':
                write_home_redis = span['duration'] / 1000.0  # review time

            if span_name == 'unique-id-service' and span_operation == 'UploadUniqueId':
                unique_s = span['duration'] / 1000.0  # rating_time
            if span_name == 'compose-post-service' and span_operation == 'UploadUniqueId':
                composepost_unique_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_unique_redis = span['duration'] / 1000.0  # review time




        # Insert duration data
        # if mis > urs and n_1 > mis and mis > mrs and crs_r > max(urs, mrs):
        # print(redis_set_data)
        redis_set_time = []
        print(text_s_timestamp, media_s_timestamp,text_s_timestamp-media_s_timestamp)
        for l in sorted(redis_set_data):redis_set_time.append(redis_set_data[l])
        if len(redis_set_time) == 6:
        # print(unique_s,composepost_unique_s,redis_set_time[2])
            sheet.write(i + 1, 0, n_1) # 'nginx_1 /ms'
            sheet.write(i + 1, 1, n_1 - (text_s_timestamp-media_s_timestamp)/1000 -text_s) # 'nginx_2 /ms'
            sheet.write(i + 1, 2, media_s-composepost_media_s) #    'media-service',
            sheet.write(i + 1, 3, composepost_media_s-redis_set_time[0]) # 'compose-post-service-uploadMedia',
            sheet.write(i + 1, 4, redis_set_time[0])# 'compose-post-service-Redis',
            sheet.write(i + 1, 5, user_s-composepost_user_s) #     'user-service',
            sheet.write(i + 1, 6, composepost_user_s-redis_set_time[1]) #     'compose-post-service-uploadCreator',
            sheet.write(i + 1, 7, redis_set_time[1])#     'compose-post-service-Redis',
            sheet.write(i + 1, 8, text_s -(composepost_s_timestamp - urlshorten_s_timestamp)/1000 - composepost_s)#     'text-service',
            sheet.write(i + 1, 9, urlshorten_s-composepost_url_s) #    'url-shorten-service',
            sheet.write(i + 1, 10, composepost_url_s-redis_set_time[3])#     'compose-post-service-uploadUrls',
            sheet.write(i + 1, 11, redis_set_time[3])#     'compose-post-service-Redis',
            sheet.write(i + 1, 12, usermention_s-composepost_usermention_s) #     'user-mention-service',
            sheet.write(i + 1, 13, composepost_usermention_s-redis_set_time[4])#     'compose-post-service-uploadUserMentions',
            sheet.write(i + 1, 14, redis_set_time[4])#     'compose-post-service-Redis',
            sheet.write(i + 1, 15, composepost_s - redis_set_time[5] - usertime_s)# 'compose-post-service-uploadText'
            sheet.write(i + 1, 16, redis_set_time[5])#   'compose-post-service-Redis',
            sheet.write(i + 1, 17, poststorage_s - poststorage_s_mongo)#    'post-storage-service',
            sheet.write(i + 1, 18, poststorage_s_mongo)#     'post-storage-service-Mongodb',
            sheet.write(i + 1, 19, usertime_s-usertime_s_mongoF)#     'post-storage-service',
            sheet.write(i + 1, 20, usertime_s_mongoF)#    'user-timeline-service-mongofind',
            sheet.write(i + 1, 21, usertime_s_mongoI) #     'user-timeline-service-mongoinsert',
            sheet.write(i + 1, 22, usertime_s_redis)# 'user-timeline-service-redis'
            sheet.write(i + 1, 23, write_home_s-socialgraph_s)
            sheet.write(i + 1, 24, socialgraph_s-socialgraph_redis-socialgraph_mongo)
            sheet.write(i + 1, 25, socialgraph_redis)
            sheet.write(i + 1, 26, socialgraph_mongo)
            sheet.write(i + 1, 27, write_home_redis)
            sheet.write(i + 1, 28, unique_s-composepost_unique_s)
            sheet.write(i + 1, 29, composepost_unique_s - redis_set_time[2])
            sheet.write(i + 1, 30, redis_set_time[2])


        # print(composepost_media_s,composepost_media_redis, composepost_media_s-composepost_media_redis)
        # else:
        #     continue

    book.save(path)


def isEnough(path, data_n=10000):
    workbook = xlrd.open_workbook(path)
    table = workbook.sheets()[0]
    nrows = table.nrows
    if nrows <= data_n:
        return False
    else:
        return True


def excel_append(data, path):
    workbook = xlrd.open_workbook(path, formatting_info=True)
    old_sheet = workbook.sheets()[0]
    nrows = old_sheet.nrows

    # print(data)
    # pprint(data)

    new_workbook = copy(workbook)
    sheet = new_workbook.get_sheet(0)

    for i, req in enumerate(data):
        processes = req['processes']
        n_1, n_2, media_s, composepost_media_s, composepost_media_redis, text_s = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        user_s, composepost_user_s, urlshorten_s, composepost_url_s, composepost_user_redis = 0.0, 0.0, 0.0, 0.0, 0.0
        composepost_url_redis, composepost_s, composepost_s_redis, poststorage_s, poststorage_s_mongo, usertime_s = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        usertime_s_mongoF, usertime_s_mongoI, usertime_s_redis, composepost_url_s, composepost_url_redis = 0.0, 0.0, 0.0, 0.0, 0.0
        write_home_redis, write_home_s, socialgraph_s, socialgraph_redis, socialgraph_mongo = 0.0, 0.0, 0.0, 0.0, 0.0
        usermention_s, composepost_usermention_s, composepost_usermention_redis = 0.0, 0.0, 0.0
        unique_s, composepost_unique_s, composepost_unique_redis = 0.0, 0.0, 0.0
        media_s_timestamp, text_s_timestamp, urlshorten_s_timestamp, composepost_s_timestamp = 0, 0, 0, 0
        # print(type(req['spans']))
        redis_set_data = {}
        for span in req['spans']:
            span_name = processes[span['processID']]['serviceName']
            span_operation = span['operationName']
            # print(span_name, span_operation)
            # if span_name == 'istio-ingressgateway' and span_operation == 'productpage.default.svc.cluster.local:9080/productpage':
            #     g_t = span['duration'] / 1000.0  # ingressgateway duration time (total time)
            if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
                composepost_media_redis = span['duration'] / 1000.0  # review time
                redis_set_data[span['startTime']] = composepost_media_redis

            if span_name == 'nginx-web-server' and span_operation == '/wrk2-api/post/compose':
                n_1 = span['duration'] / 1000.0  # productage duration (total time)

            if span_name == 'nginx-web-server' and span_operation == 'ComposePost':
                n_2 = span['duration'] / 1000.0  #

            if span_name == 'media-service' and span_operation == 'UploadMedia':
                media_s = span['duration'] / 1000.0  # detail_time
                media_s_timestamp = span['startTime']

            if span_name == 'compose-post-service' and span_operation == 'UploadMedia':
                composepost_media_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_media_redis = span['duration'] / 1000.0  # review time

            if span_name == 'user-service' and span_operation == 'UploadUserWithUserId':
                user_s = span['duration'] / 1000.0  # review_rating time
            if span_name == 'compose-post-service' and span_operation == 'UploadCreator':
                composepost_user_s = span['duration'] / 1000.0  # rating_time
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_user_redis = span['duration'] / 1000.0  # review time

            if span_name == 'text-service' and span_operation == 'UploadText':
                text_s = span['duration'] / 1000.0  # review time
                text_s_timestamp = span['startTime']
            if span_name == 'url-shorten-service' and span_operation == 'UploadUrls':
                urlshorten_s = span['duration'] / 1000.0  # rating_time
                urlshorten_s_timestamp = span['startTime']
            if span_name == 'compose-post-service' and span_operation == 'UploadUrls':
                composepost_url_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_url_redis = span['duration'] / 1000.0  # review time
            if span_name == 'user-mention-service' and span_operation == 'UploadUserMentions':
                usermention_s = span['duration'] / 1000.0  # rating_time
            if span_name == 'compose-post-service' and span_operation == 'UploadUserMentions':
                composepost_usermention_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_usermention_redis = span['duration'] / 1000.0  # review time
            if span_name == 'compose-post-service' and span_operation == 'UploadText':
                composepost_s = span['duration'] / 1000.0  #
                composepost_s_timestamp = span['startTime']
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_s_redis = span['duration'] / 1000.0  # review time
            if span_name == 'post-storage-service' and span_operation == 'StorePost':
                poststorage_s = span['duration'] / 1000.0  # review time
            if span_name == 'post-storage-service' and span_operation == 'MongoInsertPost':
                poststorage_s_mongo = span['duration'] / 1000.0  # review time

            if span_name == 'user-timeline-service' and span_operation == 'WriteUserTimeline':
                usertime_s = span['duration'] / 1000.0  # review time
            if span_name == 'user-timeline-service' and span_operation == 'MongoFindUser':
                usertime_s_mongoF = span['duration'] / 1000.0  # review time
            if span_name == 'user-timeline-service' and span_operation == 'MongoInsert':
                usertime_s_mongoI = span['duration'] / 1000.0  # review time
            if span_name == 'user-timeline-service' and span_operation == 'RedisUpdate':
                usertime_s_redis = span['duration'] / 1000.0  # review time

            if span_name == 'write-home-timeline-service' and span_operation == 'FanoutHomeTimelines':
                write_home_s = span['duration'] / 1000.0  # review time
            if span_name == 'social-graph-service' and span_operation == 'GetFollowers':
                socialgraph_s = span['duration'] / 1000.0  # review time
            if span_name == 'social-graph-service' and span_operation == 'RedisGet':
                socialgraph_redis = span['duration'] / 1000.0  # review time
            if span_name == 'social-graph-service' and span_operation == 'MongoFindUser':
                socialgraph_mongo = span['duration'] / 1000.0  # review time
            if span_name == 'write-home-timeline-service' and span_operation == 'RedisUpdate':
                write_home_redis = span['duration'] / 1000.0  # review time

            if span_name == 'unique-id-service' and span_operation == 'UploadUniqueId':
                unique_s = span['duration'] / 1000.0  # rating_time
            if span_name == 'compose-post-service' and span_operation == 'UploadUniqueId':
                composepost_unique_s = span['duration'] / 1000.0  #
            # if span_name == 'compose-post-service' and span_operation == 'RedisHashSet':
            #     composepost_unique_redis = span['duration'] / 1000.0  # review time

        # Insert duration data
        # if mis > urs and n_1 > mis and mis > mrs and crs_r > max(urs, mrs):
        # print(redis_set_data)
        redis_set_time = []
        for l in sorted(redis_set_data): redis_set_time.append(redis_set_data[l])
        # print(redis_set_time)
        # print("3")
        if len(redis_set_time) == 6:
            sheet.write(i + nrows, 0, n_1)  # 'nginx_1 /ms'
            sheet.write(i + nrows, 1, n_1 - (text_s_timestamp-media_s_timestamp)/1000 -text_s)  # 'nginx_2 /ms'
            sheet.write(i + nrows, 2, media_s - composepost_media_s)  # 'media-service',
            sheet.write(i + nrows, 3, composepost_media_s - redis_set_time[0])  # 'compose-post-service-uploadMedia',
            sheet.write(i + nrows, 4, redis_set_time[0])  # 'compose-post-service-Redis',
            sheet.write(i + nrows, 5, user_s - composepost_user_s)  # 'user-service',
            sheet.write(i + nrows, 6, composepost_user_s - redis_set_time[1])  # 'compose-post-service-uploadCreator',
            sheet.write(i + nrows, 7, redis_set_time[1])  # 'compose-post-service-Redis',
            sheet.write(i + nrows, 8, text_s -(composepost_s_timestamp - urlshorten_s_timestamp)/1000 - composepost_s)  # 'text-service',
            sheet.write(i + nrows, 9, urlshorten_s - composepost_url_s)  # 'url-shorten-service',
            sheet.write(i + nrows, 10, composepost_url_s - redis_set_time[3])  # 'compose-post-service-uploadUrls',
            sheet.write(i + nrows, 11, redis_set_time[3])  # 'compose-post-service-Redis',
            sheet.write(i + nrows, 12, usermention_s - composepost_usermention_s)  # 'user-mention-service',
            sheet.write(i + nrows, 13, composepost_usermention_s - redis_set_time[4])  # 'compose-post-service-uploadUserMentions',
            sheet.write(i + nrows, 14, redis_set_time[4])  # 'compose-post-service-Redis',
            sheet.write(i + nrows, 15, composepost_s - redis_set_time[5] - usertime_s)  # 'compose-post-service-uploadText'
            sheet.write(i + nrows, 16, redis_set_time[5])  # 'compose-post-service-Redis',
            sheet.write(i + nrows, 17, poststorage_s - poststorage_s_mongo)  # 'post-storage-service',
            sheet.write(i + nrows, 18, poststorage_s_mongo)  # 'post-storage-service-Mongodb',
            sheet.write(i + nrows, 19, usertime_s - usertime_s_mongoF)  # 'post-storage-service',
            sheet.write(i + nrows, 20, usertime_s_mongoF)  # 'user-timeline-service-mongofind',
            sheet.write(i + nrows, 21, usertime_s_mongoI)  # 'user-timeline-service-mongoinsert',
            sheet.write(i + nrows, 22, usertime_s_redis)  # 'user-timeline-service-redis'
            sheet.write(i + nrows, 23, write_home_s - socialgraph_s)
            sheet.write(i + nrows, 24, socialgraph_s - socialgraph_redis - socialgraph_mongo)
            sheet.write(i + nrows, 25, socialgraph_redis)
            sheet.write(i + nrows, 26, socialgraph_mongo)
            sheet.write(i + nrows, 27, write_home_redis)
            sheet.write(i + nrows, 28, unique_s - composepost_unique_s)
            sheet.write(i + nrows, 29, composepost_unique_s - redis_set_time[2])
            sheet.write(i + nrows, 30, redis_set_time[2])

    new_workbook.save(path)
    return nrows

if __name__ == "__main__":
    # filename = default_process()

    limit = 1500
    # path = '/home/tank-cys/cuiys_data/media-micro/conf_9_qps_500_3.xls'
    try:
        conf = sys.argv[1]
        qps = sys.argv[2]
    except:
        raise ("Faild")

    for i in range(1, 4):
        switch = True
        path = './conf_%s_qps_%s_%d.xls' % (conf, qps, i)
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
                parserdata(data_span, path)




