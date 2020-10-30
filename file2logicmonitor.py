import json
import configparser

import logicmonitor

import pprint

pp = pprint.PrettyPrinter(indent=2)

config = configparser.ConfigParser(interpolation=None)

config.read("config.ini")

api_instance = logicmonitor.LM_Session(json.loads(config['LogicMonitor']['access_id']),
                                       json.loads(config['LogicMonitor']['access_key']),
                                       json.loads(config['LogicMonitor']['company']))


filter = 'name=ASR01.SY3'
fields = 'id,name,priority'

result = api_instance.get('/device/devices', params={'size': 10, 'filter': 'name~ASR01', 'fields': ['displayName',]})
pp.pprint(result)

quit()

try:
    # get alert list
    api_response = api_instance.get_device_list(size=2, filter=filter)
    pp.pprint(api_response)
except ApiException as e:
    print("Exception when calling LMApi->getAlertList: %s\n" % e)
print('ha')
quit()
