from MicroServices.spider_for_jaeger import spiderJaeger, parseJaeger
url = "192.168.1.105"
port = 32738
limit = 10
path = '../test2.xls'
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

sn = spiderJaeger(url, port, limit)
data = sn.filterJargerTrace()
sn_data = parseJaeger(data=data, path=path, tablename=tablename)
sn_data.writeTableName()
while True:
        if sn_data.traceEnough():
            print("completed")
            break
        else:

                print("TraceNum:{}".format(sn_data.parseJaeger()))
                sn_data.parseJaeger()

