import json
import configparser
import argparse
import os
import re
import time
import sys

import lm_backend
import fs_backend
import devicegroup

import pprint

# way to map data in INI file to LM attrebutes. ('snmp.version' still does not translaed well)
ini_properties_list_lookup = dict()
LM_properties_list_lookup = dict()
properties_list = [
    {'INI': {'section': 'node', 'option': 'name', 'ReadOnly': False},
     'LM': {'customProperty': False, 'key': 'name', 'ReadOnly': False},
     'validate': lambda i: type(i) is str and i != '',
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: i, },
    {'INI': {'section': 'LogicMonitor', 'option': 'id', 'ReadOnly': False},
     'LM': {'customProperty': False, 'key': 'id', 'ReadOnly': True},
     'validate': lambda i: isinstance(int(i), int) and int(i) > 0,
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: i, },
    {'INI': {'section': 'LogicMonitor', 'option': 'parentId', 'ReadOnly': True},  # changing parent ID in folder needs special handling.
     'LM': {'customProperty': False, 'key': 'parentId', 'ReadOnly': False},
     'validate': lambda i: isinstance(int(i), int) and int(i) > 0,
     'ini_to_lm': lambda i: int(i),
     'lm_to_ini': lambda i: str(i), },
    {'INI': {'section': 'LogicMonitor', 'option': 'defaultCollectorGroupId', 'ReadOnly': False},
     'LM': {'customProperty': False, 'key': 'defaultAutoBalancedCollectorGroupId', 'ReadOnly': False},
     'validate': lambda i: isinstance(int(i), int) and int(i) >= 0,
     'ini_to_lm': lambda i: int(i),
     'lm_to_ini': lambda i: str(i), },
    {'INI': {'section': 'LogicMonitor', 'option': 'netflowCollectorGroupId', 'ReadOnly': False},
     'LM': {'customProperty': True, 'key': 'netflowCollectorGroupId', 'ReadOnly': False},
     'validate': lambda i: isinstance(int(i), int) and int(i) >= 0,
     'ini_to_lm': lambda i: int(i),
     'lm_to_ini': lambda i: str(i), },
    {'INI': {'section': 'node', 'option': 'CorrelationID', 'ReadOnly': False},
     'LM': {'customProperty': True, 'key': 'servicenow.company', 'ReadOnly': False},
     'validate': lambda i: re.match("\A[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z",i),
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: i, },
    {'INI': {'section': 'node', 'option': 'description', 'ReadOnly': False},  # comment
     'LM': {'customProperty': False, 'key': 'description', 'ReadOnly': False},
     'validate': lambda i: type(i) is str or i is None,
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: i, },
    {'INI': {'section': 'node', 'option': 'subPath', 'ReadOnly': True},  # never synced between LM and Disk so 'ReadOnly' on both ends
     'LM': {'customProperty': False, 'key': 'subPath', 'ReadOnly': True},
     'validate': lambda i: type(i) is str,
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: i, },
    {'INI': {'section': 'SNMPv2', 'option': 'snmpv2community', 'ReadOnly': True},  # SNMP comunity, not extractable from LM
     'LM': {'customProperty': True, 'key': 'snmp.community', 'ReadOnly': False},
     'validate': lambda i: type(i) is str and i != '',
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: ''},
    {'INI': {'section': 'SNMPv3', 'option': 'snmpv3username', 'ReadOnly': False},  # SNMPv3 username
     'LM': {'customProperty': True, 'key': 'snmp.security', 'ReadOnly': False},
     'validate': lambda i: type(i) is str and i != '',
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: i},
    {'INI': {'section': 'SNMPv3', 'option': 'snmpv3authenticationmethod', 'ReadOnly': False},  # SNMPv3 auth method
     'LM': {'customProperty': True, 'key': 'snmp.auth', 'ReadOnly': False},
     'validate': lambda i: type(i) is str and i != '',
     'ini_to_lm': lambda i: ini_SNMPv3_auth_method_mapping[i],
     'lm_to_ini': lambda i: LM_SNMPv3_auth_method_mapping[i]},
    {'INI': {'section': 'SNMPv3', 'option': 'snmpv3authenticationkey', 'ReadOnly': True},  # # SNMPv3  auth key, not extractable from LM
     'LM': {'customProperty': True, 'key': 'snmp.authToken', 'ReadOnly': False},
     'validate': lambda i: type(i) is str and i != '',
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: ''},
    {'INI': {'section': 'SNMPv3', 'option': 'snmpv3privacymethod', 'ReadOnly': False},  # SNMPv3 encryption method
     'LM': {'customProperty': True, 'key': 'snmp.priv', 'ReadOnly': False},
     'validate': lambda i: type(i) is str and i != '',
     'ini_to_lm': lambda i: ini_SNMPv3_encryption_method_mapping[i],
     'lm_to_ini': lambda i: LM_SNMPv3_encryption_method_mapping[i]},
    {'INI': {'section': 'SNMPv3', 'option': 'snmpv3privacykey', 'ReadOnly': True},  # # SNMPv3  encryption key, not extractable from LM
     'LM': {'customProperty': True, 'key': 'snmp.privToken', 'ReadOnly': False},
     'validate': lambda i: type(i) is str and i != '',
     'ini_to_lm': lambda i: i,
     'lm_to_ini': lambda i: ''},
]

ini_SNMPv3_auth_method_mapping = {
    'SHA1': 'SHA',
    'MD5': 'MD5',
    'None': ''
}
LM_SNMPv3_auth_method_mapping = {}
ini_SNMPv3_encryption_method_mapping = {
    'AES128': 'AES',
    'DES56': 'DES',
    'None': ''
}
LM_SNMPv3_encryption_method_mapping = {}

collectorsid = (7,)
dynamic_group_Ids = set()


def dict_invert(input):  # iverting keys.
    result = dict()
    for key in input.keys():
        if input[key] not in result.keys():
            result[input[key]] = key
        else:
            print("ERROR: Can't invert dict due to no uniq keys:", key, "\n", pp.pformat(input))
            quit(1)
    return(result)


def properties_list_lookup_calculation():
    for index, value in enumerate(properties_list):  # can use try, but to not like it here,
        if value['INI']['section'] not in ini_properties_list_lookup.keys():
            ini_properties_list_lookup[value['INI']['section']] = {}
        ini_properties_list_lookup[properties_list[index]['INI']['section']][properties_list[index]['INI']['option']] = index
        if value['LM']['customProperty'] not in LM_properties_list_lookup.keys():
            LM_properties_list_lookup[value['LM']['customProperty']] = {}
        LM_properties_list_lookup[value['LM']['customProperty']][value['LM']['key']] = index


def update_dynamic_groups_list(list):
    # should not go directly to API gfor groups, but I do.
    to_check = set(list) - dynamic_group_Ids
    for group_id in to_check:
        result = api_instance.get('/device/groups/'+str(int(group_id)), params={'fields': "appliesTo,fullPath", })
        if result['status'] != 200:
            print('It was an erorr', pp.pformat(result))
            quit(1)
        if result['data']['appliesTo'] != '':  # group is dynamic
            dynamic_group_Ids.add(group_id)
            print('New dynamic group found:', result['data']['fullPath'])



def node_handler(entry_name, sub_path, root_path, parent, collectorId, offset):
    path = root_path + '/' + sub_path + '/' + entry_name

    node_config = configparser.RawConfigParser(interpolation=None)
    node_config.optionxform = lambda option: option  # case sentitive options
    node_config.read(path)
    if not re.match("\w.*\.ini\Z", entry_name):
        print("What?", entry_name)
        quit(1)

    lm_needs_update = False
    lm_patchFields = set()
    disk_needs_update = False

    if 'LogicMonitor' not in node_config.sections():
        node_config['LogicMonitor'] = {}
        disk_needs_update = True

    payload = {}
    payload['customProperties'] = []
    result = None

    if 'id' in node_config.options('LogicMonitor'):  # lets try to check is that node still exisits
        result = api_instance.get('/device/devices/' + str(node_config['LogicMonitor']['id']))
        if result['status'] == 200:  # node exisits.

            InSyncWithBackend = False  # Let's find who is The Boss
            for i in result['data']["customProperties"]:
                if i['name'] == "InSyncWithBackend" and i['value'] == 'Yes':
                    InSyncWithBackend = True
                    break

            # device renamed
            if result['data']['displayName'] != entry_name[:-4]:  # Node was renamed
                if InSyncWithBackend:  # file backend is leading
                    payload['displayName'] = str(entry_name[:-4])
                    lm_patchFields.add('displayName')
                    lm_needs_update = True
                else:
                    print("Node have been renamed in LM, can't handle it yet (but itis in the plans). Quiting")
                    quit(1)

            # device was moved to different group.
            hostGroupIds = set(result['data']['hostGroupIds'].split(',')) - dynamic_group_Ids
            if len(hostGroupIds) > 1:  # host probaly nmember of some unknown dynamic groups.
                update_dynamic_groups_list(hostGroupIds)
                hostGroupIds = set(result['data']['hostGroupIds'].split(',')) - dynamic_group_Ids
                if len(hostGroupIds) > 1:
                    print("Node is member more than one static group in LM, have no idea what to do with it. Quiting")
                    quit(1)

            if str(parent.data['id']) not in hostGroupIds:  # group list need to be patched. (I'm assuming that hostGroupId always present )
                if InSyncWithBackend:  # file backend is leading
                    payload['hostGroupIds'] = str(parent.data['id'])
                    lm_patchFields.add('hostGroupIds')
                    node_config['LogicMonitor']['hostGroupIds'] = str(parent.data['id'])
                    disk_needs_update = True
                else:
                    print("Node have moved in LM, can't handle it yet (but itis in the plans). Quiting")
                    quit(1)

            hostGroupIds_ini = set(node_config['LogicMonitor']['hostGroupIds'].split(','))
            if len(hostGroupIds_ini) > 1:
                print("Node is member more than one group in file, have no idea what to do with it. Quiting")
                quit(1)
            if 'hostGroupId' in node_config.options('LogicMonitor'):  # this is simple, should be always follow folder id.
                if node_config['LogicMonitor']['hostGroupId'] != str(parent.data['id']):
                    node_config['LogicMonitor']['hostGroupId'] = str(parent.data['id'])
                    print(1)
                    disk_needs_update = True

            # let's handle collector move.
            if 'preferredCollectorGroupId' in node_config.options('LogicMonitor'):
                if str(node_config['LogicMonitor']['preferredCollectorGroupId']) != str(result['data']['preferredCollectorGroupId']):
                    node_config['LogicMonitor']['preferredCollectorGroupId'] == str(result['data']['preferredCollectorGroupId'])
                    print(2)
                    disk_needs_update = True
            else:
                node_config['LogicMonitor']['preferredCollectorGroupId'] != result['data']['preferredCollectorGroupId']
                disk_needs_update = True

            if lm_needs_update:
                payload['customProperties'].append({'name': "InSyncWithBackend", 'value': 'Yes'})
                result = api_instance.patch('/device/devices/' + str(node_config['LogicMonitor']['id']),
                                            payload=payload,
                                            params={'patchFields': ','.join(lm_patchFields | set(('customProperties',))),
                                            'opType': 'replace'})
                if result['status'] != 200:
                    print('It was an error while updating node data', pp.pformat(result))
                    quit(1)
                print(' '.ljust(offset), '| ', entry_name, '- found, LM config updated. Fields: ', ','.join(lm_patchFields))
                pp.pprint(payload)
            else:
                print(' '.ljust(offset), '| ', entry_name, '- found, nothing need to be done in LM')

        elif result['status'] == 1404:  # Node not found, let's create it.
            result = None
        else:
            print('Unexpected responce from LM when trying to find exisiting node.')
            pp.pprint(result)
            quit(1)

    if result is None:  # no id in the file or node not found by exisiting ID. So try to create it.
        payload['displayName'] = entry_name[:-4]  # it must end by .ini. Regex is cheked
        payload['name'] = str(node_config['node']['ipv4address'])
        # payload['description'] = 'Test Host'
        # payload['preferredCollectorGroupId'] = '6'
        payload['preferredCollectorId'] = str(collectorId)
        payload['hostGroupIds'] = str(parent.data['id'])

        if "SNMPv3" in node_config.sections():
            print(' '.ljust(offset), '| ', entry_name, '- file', node_config['node']['ipv4address'], "SNMPv3")
            payload['customProperties'] = [{'name': 'snmp.version', 'value': 'v3'}]
            # FIXME no bloody static list. Use same approach as for group attributes.
            if node_config.has_option('SNMPv3', 'snmpv3username'):
                payload['customProperties'].append({'name': 'snmp.security', 'value': node_config['SNMPv3']['snmpv3username']})
            if node_config.has_option('SNMPv3', 'snmpv3authenticationmethod'):
                payload['customProperties'].append({'name': 'snmp.auth', 'value': ini_SNMPv3_auth_method_mapping[node_config['SNMPv3']['snmpv3authenticationmethod']]})
            if node_config.has_option('SNMPv3', 'snmpv3authenticationkey'):
                payload['customProperties'].append({'name': 'snmp.authToken', 'value': node_config['SNMPv3']['snmpv3authenticationkey']})
            if node_config.has_option('SNMPv3', 'snmpv3privacymethod'):
                payload['customProperties'].append({'name': 'snmp.priv', 'value': ini_SNMPv3_encryption_method_mapping[node_config['SNMPv3']['snmpv3privacymethod']]})
            if node_config.has_option('SNMPv3', 'snmpv3privacykey'):
                payload['customProperties'].append(
                    {'name': 'snmp.privToken', 'value': node_config['SNMPv3']['snmpv3privacykey']})
        elif "SNMPv2" in node_config.sections():
            print(' '.ljust(offset), '| ', entry_name, '- file', node_config['node']['ipv4address'], "SNMPv2")
            payload['customProperties'] = [{'name': 'snmp.version', 'value': 'v2c'}]
            if node_config.has_option('SNMPv2', 'snmp.community'):
                payload['customProperties'].append({'name': 'snmp.community', 'value': node_config['SNMPv2']['snmp.community']})
        else:  # we will just use ping
            print(' '.ljust(offset), '| ', entry_name, '- file', node_config['node']['ipv4address'], "Ping")
            payload['customProperties'] = [{'name': 'snmp.version', 'value': ''}]

        payload['customProperties'].append({'name': "InSyncWithBackend", 'value': 'Yes'})
        result = api_instance.post('/device/devices', payload=payload)
        # pp.pprint(result)
        if result['status'] != 200:
            print('It was an erorr', pp.pformat(result))
            quit(1)

        print(' '.ljust(offset), '| ', entry_name, '- created in LM')
        # updating disk.
        node_config['LogicMonitor']['id'] = str(result['data']['id'])
        node_config['LogicMonitor']['hostGroupIds'] = str(parent.data['id'])
        node_config['LogicMonitor']['preferredCollectorGroupId'] = str(result['data']['preferredCollectorGroupId'])

        device_id = int(result['data']['id'])
        result = api_instance.post('/device/devices/' + str(device_id) + '/scheduleAutoDiscovery')

        disk_needs_update = True
        lm_needs_update = False


    if disk_needs_update:
        # let's update data on disk.
        with open(path, 'w') as configfile:
            node_config.write(configfile)
        print(' '.ljust(offset), '| ', entry_name, '- on disk .ini updated')


def tree_runner(sub_path, root_path, parent, offset=0):
    path = root_path + '/' + sub_path
    for entry in os.scandir(path=path):
        if entry.is_file():
            if re.match("\w.*\.ini\Z", entry.name):
                node_handler(entry.name, sub_path, root_path, parent, 73, offset)
                pass
            elif entry.name == '.group.ini':
                continue
            else:
                continue
        elif entry.is_dir():
            if re.match("\A\..*\Z", entry.name): # we do not want to desent to .git folders.
                continue
            group_ini = entry.path + '/.group.ini'
            group_config = configparser.RawConfigParser(interpolation=None)
            group_config.optionxform = lambda option: option  # case sentitive options

            lm_needs_update = False
            lm_patchFields = set()
            disk_needs_update = False

            if os.access(group_ini, os.F_OK):
                # group.ini exists
                group_config.read(group_ini)
                if not group_config.has_section('node'):
                    group_config['node'] = {}
                if not group_config.has_section('LogicMonitor'):
                    group_config['LogicMonitor'] = {}

                if not group_config.has_option('node', 'name') or group_config['node']['name'] != entry.name:  # creating
                    group_config['node']['name'] = entry.name
                    disk_needs_update = True
                if not group_config.has_option('node', 'subPath') or \
                        group_config['node']['subPath'] != sub_path + ('/' if sub_path != '' else '') + entry.name:  # creating
                    group_config['node']['subPath'] = sub_path + ('/' if sub_path != '' else '') + entry.name
                    disk_needs_update = True

            else:  # lets create group config.
                group_config['node'] = {}
                group_config['node']['name'] = entry.name
                group_config['LogicMonitor'] = {}
                with open(group_ini, 'w') as configfile:
                    group_config.write(configfile)
                print(' '.ljust(offset), '| ', entry.name, '- dir Config created')

            # Now we have on disk config reagerdeles did it exists or created.
            # lests ask LM about this group.
            if 'id' in group_config.options('LogicMonitor'):  # search exisitng group by Id. Parent ID may change.
                groupdata = {
                  "id": str(group_config['LogicMonitor']['id']),
                  "customProperties": []
                }
            else:  # search by name
                groupdata = {
                  "name": entry.name,
                  "parentId": parent.data['id'],
                  "customProperties": []
                }

            dg = lm_backend.DeviceGroup(api_instance, deviceGroup=devicegroup.DeviceGroup(data=groupdata))
            dg.get(raiseWhenNotFound=False)
            if dg.data['id'] is None:  # Group does not exists, let's create it just basic sketch. Yes we have to patch it later. wich is longer then creating it in one go. But this approach is better for code readability.
                print('LM Group not found, creating')
                InSyncWithBackend = True
                groupdata["customProperties"].append({"name": "InSyncWithBackend",
                                                      "value": "Yes"})
                dg = lm_backend.DeviceGroup(api_instance, deviceGroup=devicegroup.DeviceGroup(data=groupdata))  # better to recreate classe as data was changed.
                dg.put()  # it will raise exception if something is wrong.
                print('Added group: ' + dg.data['fullPath'])
            else:
                print('Found previously created group: ' + dg.data['fullPath'])
                # need to decide to what direction data should be copied. LM do disl of Disk to LM
                InSyncWithBackend = False
                for i in dg.data["customProperties"]:
                    if i['name'] == "InSyncWithBackend" and i['value'] == 'Yes':
                        InSyncWithBackend = True
                        break

            # in this moment "group_config" contans data loaded drom disk and "gd" is object linked to LM.  Let's try to sync it.
            # If key entry missed in one of location data will be copied to other one. If both have a key and values are differnt copy direction will be contrlled by InSyncWithBackend key in LM
            # if it present and true than disk data will be used otherwise LM will be copied to disk.

            # let's transform LM "Custom properites to normal dict"
            lm_extra_dict = {}
            for i in dg.data["customProperties"]:
                if i['name'] in lm_extra_dict.keys():
                    print("Dublicate key values in LM customProperties. Have no idea what to do with it. Quiting\n", dg.data)
                    quit(1)
                else:
                    if not re.match("^\**$", i['value']): #this one of "password" type parameters for wich LM replaces values with *****
                        lm_extra_dict[i['name']] = i['value']
                    else:
                        lm_extra_dict[i['name']] = None

            # only data wich we importing for folder structure is node name, LM will be updated normal way
            if group_config['node']['name'] != entry.name:  # "name" field in .ini is out of sync.
                disk_needs_update = True
                group_config['node']['name'] = entry.name
            # FIXME.  If group is renamed in LM, It need a code to handle it.
            if 'parentId' in group_config.options('LogicMonitor'):
                if str(parent.data['id']) != group_config['LogicMonitor']['parentId']:  # group was moved on disk.
                    disk_needs_update = True
                    group_config['LogicMonitor']['parentId'] = str(parent.data['id'])
                if str(dg.data['parentId']) != str(parent.data['id']) and not InSyncWithBackend: # groupe was moved in LM
                    print('Cant handle group reloaction in LM yet. Quiting')
                    quit(1)
                else:
                    pass  # copy from Disk to LM will handled by same code as any other attribute
            else:
                group_config['LogicMonitor']['parentId'] = str(parent.data['id'])  # should not be ever called during normal operation.
                disk_needs_update = True
            # FIXME add code to handle group was moved in LM.

            # option set is SET of indexes refering to values in "properties_list" dictionary
            disk_set = set()
            # Anyhing wich not defined properties_list should be removed from INI file. Lets keep data clean.
            # We will build disk_set at same time.
            for section in group_config.sections():
                if section not in ini_properties_list_lookup.keys():  # whole section need to be deleted
                    del group_config[section]
                    disk_needs_update = True
                    continue
                for option in group_config.options(section):
                    if option in ini_properties_list_lookup[section].keys():  # i do not what to use try: here
                        disk_set.add(ini_properties_list_lookup[section][option])
                    else:  # If element is not in ther "properties_list" we do not care about it
                        del group_config[section][option]
                        disk_needs_update = True


            lm_main_set = set(map(lambda i: LM_properties_list_lookup[False][i], set(dg.data.keys()) & set(LM_properties_list_lookup[False].keys())))
            lm_extra_set = set(map(lambda i: LM_properties_list_lookup[True][i], set(lm_extra_dict.keys()) & set(LM_properties_list_lookup[True].keys())))

            for key in disk_set | lm_main_set | lm_extra_set:  # element present any of sets.
                if properties_list[key]['INI']['ReadOnly'] and properties_list[key]['LM']['ReadOnly']:  # if Attribute Readonly in LM and Disk then no need to copy,
                    continue
                is_customProperty = key in lm_extra_set
                if key in lm_main_set | lm_extra_set:
                    lm_value = lm_extra_dict[properties_list[key]['LM']['key']] \
                        if is_customProperty else dg.data[properties_list[key]['LM']['key']]
                if key in disk_set:
                    disk_value = group_config[properties_list[key]['INI']['section']][properties_list[key]['INI']['option']]
                if key in (disk_set & (lm_main_set | lm_extra_set)):  # element present in both sets.
                    if str(lm_value) != str(disk_value):  # FIXME: actually need to translate to some intermideate from to be comparable.
                        if InSyncWithBackend:  # data is copied to LM from disk.
                            print("Key", properties_list[key]['LM']['key'], 'present in both lists, copy it to LM ', not properties_list[key]['LM']['ReadOnly'])
                            if not properties_list[key]['LM']['ReadOnly']:
                                lm_needs_update = True
                                if not is_customProperty:
                                    dg.data[properties_list[key]['LM']['key']] = properties_list[key]['ini_to_lm'](disk_value)
                                    lm_patchFields.add(str(properties_list[key]['LM']['key']))
                                else:
                                    keyFound = False
                                    for CustomProperty in dg.data['customProperties']:
                                        if CustomProperty['name'] == properties_list[key]['LM']['key']:  # same key already exists
                                            CustomProperty['value'] = properties_list[key]['ini_to_lm'](disk_value)
                                            keyFound = True
                                            break  # Let's hope that there is no dublikate keys already.
                                    if not keyFound:
                                        dg.data['customProperties'].append(
                                            {
                                                'name': properties_list[key]['LM']['key'],
                                                'value': properties_list[key]['ini_to_lm'](disk_value)
                                            })
                                    lm_patchFields.add('customProperties')
                        else:  # data is copied to disk from LM
                            print("Key", properties_list[key]['LM']['key'], 'present in both lists, copy it to Disk', not properties_list[key]['INI']['ReadOnly'])
                            lm_needs_update = True # just to set "InSyncWithBackend" in LM
                            if not properties_list[key]['INI']['ReadOnly']:
                                disk_needs_update = True
                                group_config[properties_list[key]['INI']['section']][properties_list[key]['INI']['option']] = str(properties_list[key]['lm_to_ini'](lm_value))
                elif key in ((lm_main_set | lm_extra_set)):  # present in LM but not on disk
                    print("Key", properties_list[key]['LM']['key'], 'not present on disk, copy it from LM', not properties_list[key]['INI']['ReadOnly'])
                    if not properties_list[key]['INI']['ReadOnly']:
                        disk_needs_update = True
                        group_config[properties_list[key]['INI']['section']][properties_list[key]['INI']['option']] = str(properties_list[key]['lm_to_ini'](lm_value))
                elif key in disk_set - (lm_main_set | lm_extra_set):  # present on disk but not in LM. We will update LM regardelses of InSyncWithBackend value, as it is new values.
                    print("Key", properties_list[key]['LM']['key'], 'present only on disk, copy it to LM ', not properties_list[key]['LM']['ReadOnly'])
                    if not properties_list[key]['LM']['ReadOnly']:
                        lm_needs_update = True
                        if properties_list[key]['LM']['customProperty']:
                            dg.data['customProperties'].append(
                                {
                                    'name': properties_list[key]['LM']['key'],
                                    'value': properties_list[key]['ini_to_lm'](disk_value)
                                })
                            lm_patchFields.add('customProperties')
                        else:
                            dg.data[properties_list[key]['LM']['key']] = properties_list[key]['ini_to_lm'](disk_value)
                            lm_patchFields.add(str(properties_list[key]['LM']['key']))
                else:
                    print('This should not happen #1, Quiting')
                    quit(1)

            if lm_needs_update:
                group_config['node']['LMSync_Timestamp'] = str(dg.data['LMSync_Timestamp'])
                dg.data['LMSync_Timestamp'] = int(time.time())
                if "InSyncWithBackend" not in lm_extra_dict.keys():
                    dg.data['customProperties'].append({'name': "InSyncWithBackend", 'value': 'Yes'})
                lm_patchFields.add('customProperties')

            if disk_needs_update:
                lm_patchFields.add('customProperties')
                dg.data['FSSync_Timestamp'] = int(time.time())
                group_config['node']['FSSync_Timestamp'] = str(dg.data['FSSync_Timestamp'])

            if disk_needs_update or lm_needs_update:
                # let's update data on disk. At least time stamp need to be updated.
                with open(group_ini, 'w') as configfile:
                    group_config.write(configfile)
                # print(' '.ljust(offset), '| ', entry.name, '- dir Config updated')
                dg.patch(patchFields=lm_patchFields)
                print(' '.ljust(offset), '| ', entry.name, '- data in LM and Disk was updated')

            tree_runner(sub_path + ('/' if sub_path != '' else '') + entry.name, root_path, dg, offset=offset + 3)
        else:
            print(entry.name, " is not file or directory, I have no idea what to do it with it")
            quit(1)


# main()

pp = pprint.PrettyPrinter(indent=2)

LM_SNMPv3_auth_method_mapping = dict_invert(ini_SNMPv3_auth_method_mapping)
LM_SNMPv3_encryption_method_mapping = dict_invert(ini_SNMPv3_encryption_method_mapping)
properties_list_lookup_calculation()

# if subpath provided in command line start there id nothing provided just run from root folder.

parser = argparse.ArgumentParser(description='Import Nodes to Logic MOnitor.')
parser.add_argument('subpath', nargs='?', default="", help='path to folder to process relative to root folder from config.ini')
args = vars(parser.parse_args())
start_at = args['subpath']
start_at = ("/" + start_at) if start_at != "" else ""
# calculate_LM_ini_customProperties()

config = configparser.ConfigParser(interpolation=None)

config.read("config.ini")

api_instance = lm_backend.API_Session(json.loads(config['LogicMonitor']['access_id']),
                                      json.loads(config['LogicMonitor']['access_key']),
                                      json.loads(config['LogicMonitor']['company']))
groupdata = {
  "fullPath": json.loads(config['LogicMonitor']['RootPath']) + start_at
}
dg = lm_backend.DeviceGroup(api_instance, deviceGroup=devicegroup.DeviceGroup(data=groupdata))
dg.get(raiseWhenNotFound=False)
if dg.data['id'] is None:  # Group does not exists
    print("Root group was not found, Quiting")
    quit(1)
else:
    print('Found root group: ' + dg.data['fullPath'])

# print(dynamic_group_Ids)
# update_dynamic_groups_list(set((12, 1183, 2077, 5, 1185)))
# print(dynamic_group_Ids)

tree_runner('', str(config['FileSystemBackend']['rootpath']).replace('"', '') + start_at, dg)

quit()
