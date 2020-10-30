import time
import json
import configparser

import logicmonitor_sdk
from logicmonitor_sdk.rest import ApiException

import pprint

pp = pprint.PrettyPrinter(indent=2)

config = configparser.ConfigParser(interpolation=None)

config.read("config.ini")

print(json.loads(config['LogicMonitor']['company']))

# Configure API key authorization: LMv1
configuration = logicmonitor_sdk.Configuration()
configuration.company = json.loads(config['LogicMonitor']['company'])
configuration.access_id = json.loads(config['LogicMonitor']['access_id'])
configuration.access_key = json.loads(config['LogicMonitor']['access_key'])

# create an instance of the API class
api_instance = logicmonitor_sdk.LMApi(logicmonitor_sdk.ApiClient(configuration))

try:
    # get alert list
    api_response = api_instance.get_device_list(size=2)
    pp.pprint(api_response)
except ApiException as e:
    print("Exception when calling LMApi->getAlertList: %s\n" % e)
print('ha')
quit()
