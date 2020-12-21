import configparser
config = configparser.ConfigParser()
cfgname = "config.ini"
config.read(cfgname, encoding='utf-8')
all_sections = config.sections()
print(all_sections)
print(config.options("LC"))
# options = config.options("SPARK")
#
# if not config.has_section('remark'):
#     config.add_section('remark')
# config.set('remark', 'info', 'ok')
# config.write(open(cfgname, 'w'))
# remark = config.items('remark')
# print(remark)
# print('sections: ', all_sections)
# print(config.get("SPARK","ip"))