import time
import json

import lm_backend
import devicegroup


class DeviceGroup(devicegroup.DeviceGroup):

    __RO_attributes__ = frozenset((
        'id',
        'awsTestResult',
        'azureTestResult',
        'autoVisualResult',
        'awsTestResultCode',
        'azureTestResultCode',
        'createdOn',
        'fullPath',
        'numOfHosts'
        'numOfAWSDevices',
        "numOfAzureDevices",
        "numOfGcpDevices",
        "numOfDirectDevices",
        "numOfDirectSubGroups",
        "effectiveAlertEnabled",
        "sdtStatus",
        "alertStatus",
        "alertStatusPriority",  # not shure what does it do maybe not RO
        "clusterAlertStatus",
        "clusterAlertStatusPriority",  # not shure what does it do maybe not RO
        "alertDisableStatus",
        "alertingDisabledOn",  # not shure what does it do maybe not RO
        "groupStatus",
        "subGroups",
        "defaultCollectorDescription",
    ))

    def __init__(self, LM_Session, id=None, fullPath=None, deviceGroup=None):
        ''' can be created ether by specifying LM group ID or fullPath, or from base class'''
        # TODO - proper handling when constructor called and deviceGroup is lm_backend.DeviceGroup class

        if id is None and fullPath is None and deviceGroup is None:
            print(id, fullPath, deviceGroup)
            raise lm_backend.LM_Session_Error('ether id,filePath or deviceGroup need to be provided')
            quit(1)

        self.LM_Session = LM_Session
        # know it is not a right way, but have no idea how to proprly poulate fields from nase class
        if deviceGroup is not None:
            if issubclass(deviceGroup.__class__, devicegroup.DeviceGroup):
                super(lm_backend.DeviceGroup, self).clone(deviceGroup)
            else:
                raise lm_backend.LM_Session_Error('"deviceGroup" bust be subclass of devicegroup.DeviceGroup. Got: ' + str(type(deviceGroup)))
        else:
            super(lm_backend.DeviceGroup, self).__init__()
            # use bloody self.get() !!!!
            if id is not None:
                self.data['id'] = int(id)
                self.get(searchOrder=['id', ])
            elif fullPath is not None:
                self.data['fullPath'] = str(fullPath)
                self.get(searchOrder=['fullPath', ])
            else:  # we already checked that some of paramiters are not none.
                raise lm_backend.LM_Session_Internal_Error("This should not happen ever")
            # copying of data from LM

    def clone(self, source):
        '''just copied data to self from other instance of same class'''
        # should I use deep copy instaed?
        if issubclass(source.__class__, lm_backend.DeviceGroup):
            super(lm_backend.DeviceGroup, self).clone(source)
            self.LM_Session = source.LM_Session
        else:
            raise lm_backend.LM_Session_Internal_Error('Expected subclass of <class lm_backend.DeviceGroup>, got {}.'.format(type(source)))

    def get(self, searchOrder=['id', 'fullPath', "name"], raiseWhenNotFound=True):
        ''' try to populate intance via LM API'''
        ''' searchOrder - controls what field and in what order use to search, when found other fileds will be updated by data from LM
            'id' - will use "self.data['id']" to match group (fastest)
            'fullPath' - will use "self.data['fullPath']" to find group
            'name' - will use "self.data['name']" and "self.data['parentId']" to find group
            raiseWhenNotFound if True will rise  LM_Session_Query_Error if group can't be found, if False just set data['LMSync_Timestamp'] to 0 and exit.
        '''
        if len(searchOrder) < 1 or len(searchOrder) > 3:
            raise lm_backend.LM_Session_Query_Error('Query error: searchOrder must contain between 1 to 3 entries', )
        for method in searchOrder:
            if method == 'id' and 'id' in self.data:
                if self.data['id'] is None:
                    continue
                result = self.LM_Session.get('/device/groups/' + str(self.data['id']))
                if result['status'] == 1069 and raiseWhenNotFound:
                    raise lm_backend.LM_Session_Query_Error('The hostgroup ID ' + str(self.data['id']) + ' is not found')
                    quit(1)
                elif result['status'] not in (200, 1069):
                    raise lm_backend.LM_Session_Query_Error('Query error: ' + result['errmsg'])
                    quit(1)
                else:
                    self.__update_data__(result['data'])
                    self.data['Update_Timestamp'] = int(time.time())
                    self.data['LMSync_Timestamp'] = self.data['Update_Timestamp']
                    return
            if (method == 'fullPath' and 'fullPath' in self.data) or \
               (method == 'name' and 'name' in self.data and 'parentId' in self.data):
                try:
                    filter = ('fullPath:"' + str(self.data['fullPath']) + '"') if (method == 'fullPath') else \
                        ('name:' + str(self.data['name']) + ',' + 'parentId:' + str(self.data['parentId']))
                except TypeError:
                    # not sure is it safe. should cach situation when some od data['xx'] are None or wrong type
                    continue
                result = self.LM_Session.get('/device/groups', params={'filter': filter})
                # print(json.dumps(result, indent=4))
                if result['status'] != 200:
                    print(result)
                    raise lm_backend.LM_Session_Query_Error('Query error: ' + result['errmsg'])
                    quit(1)
                if result['data']['total'] > 1:
                    raise lm_backend.LM_Session_Database_Error('LM API return more than 1 result in group search "' + self.data['fullPath'] + '"')
                    quit(1)
                elif result['data']['total'] == 0:
                    # nothing found, let's try other method
                    continue
                else:
                    self.__update_data__(result['data']['items'][0])
                    self.data['Update_Timestamp'] = int(time.time())
                    self.data['LMSync_Timestamp'] = self.data['Update_Timestamp']
                    return
        # if we got here, means none of search methods returned any results
        self.data['LMSync_Timestamp'] = 0
        if raiseWhenNotFound:
            raise lm_backend.LM_Session_Query_Error('Unable match object' + str(self) + ' with LM database')
            quit(1)

    def put(self, raiseIfExists=True):
        ''' Creates group in LM, based on fullPath or (parentId + name) '''
        ''' Id is ignored. if instance have both fullPath and (parentId + name), parentID takes priority
            if raiseIfExists is True and group already exist on same path then LM_Session_Query_Error will rised
            if raiseIfExists is False and group already exist on same path then set data['LMSync_Timestamp'] to 0 and exit
            If LM API returns an error exception will be always raised.
            After creation Read Only data get populated
        '''
        RW_data = {}
        for key in self.data.keys():
            if key not in lm_backend.DeviceGroup.__RO_attributes__ and self.data[key] is not None:
                RW_data[key] = self.data[key]

        if set(('parentId', 'name')).issubset(set(self.data.keys())):
            if 'fullPath' in self.data.keys():
                del self.data['fullPath']
            result = self.LM_Session.post('/device/groups', payload=RW_data)
            if result['status'] != 200:
                raise lm_backend.LM_Session_Query_Error('Query error: ' + result['errmsg'] + ' Result: ' + str(result['status']))
                quit(1)
            else:
                self.__update_data__(result['data'])
                self.data['Update_Timestamp'] = int(time.time())
                self.data['LMSync_Timestamp'] = self.data['Update_Timestamp']
        elif 'fullPath' in self.data.keys():
            raise lm_backend.LM_Session_Query_Error("Not implemented")
        else:
            raise lm_backend.LM_Session_Query_Error('FullPath or (parentId + name) is requred to create group')
            quit(1)

    def patch(self, patchFields=None, raiseWhenNotFound=True):
        ''' Update exisiting LM Group by data from instance '''
        ''' Both Id and fullPath have to match data in LM, otherwise query will fail
        If LM API returns an error exception will be always raised.
        After succesful Read Only data get populated by second self.get() request
        patchFields list of field wich need to be updated. should be list or set. If it is None, all fids will be updated.
        '''
        if patchFields is None:
            patchFields = set(self.data.keys())
        RW_data = {}
        for key in set(self.data.keys()) & set(patchFields):  # only data from patchField are get copied.
            if key not in lm_backend.DeviceGroup.__RO_attributes__ and self.data[key] is not None:
                RW_data[key] = self.data[key]

        if 'id' in self.data.keys():
            if 'fullPath' in self.data.keys():
                del self.data['fullPath']
            result = self.LM_Session.patch('/device/groups/' + str(self.data['id']), payload=RW_data, params={'patchFields': ','.join(patchFields), 'opType': 'replace'})
            if result['status'] != 200:
                raise lm_backend.LM_Session_Query_Error('Query error: ' + result['errmsg'] + ' Result: ' + str(result['status']))
                quit(1)
            else:
                self.__update_data__(result['data'])
                self.data['Update_Timestamp'] = int(time.time())
                self.data['LMSync_Timestamp'] = self.data['Update_Timestamp']
        else:
            raise lm_backend.LM_Session_Query_Error('"id" is requred to update group data')
            quit(1)
        pass

if __name__ == '__main__':
    quit()
