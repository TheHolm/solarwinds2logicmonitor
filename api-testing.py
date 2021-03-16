import json
import configparser

import lm_backend

import pprint

# main()

pp = pprint.PrettyPrinter(indent=2)

# calculate_LM_ini_customProperties()

config = configparser.ConfigParser(interpolation=None)

config.read("config.ini")

api_instance = lm_backend.API_Session(json.loads(config['LogicMonitor']['access_id']),
                                      json.loads(config['LogicMonitor']['access_key']),
                                      json.loads(config['LogicMonitor']['company']))


payload = {}
payload['customProperties'] = []
result = None

result = api_instance.get('/device/groups/2381' + '')
# result = api_instance.get('/device/devices/3669' + '')
print('-' * 10)
pp.pprint(result)

quit()
