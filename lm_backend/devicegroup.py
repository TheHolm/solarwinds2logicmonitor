import time
import json

import lm_backend
import devicegroup


class DeviceGroup(devicegroup.DeviceGroup):

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
                self.get(searchOrder=['ullPath', ])
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

    def get(self, searchOrder=['id', 'fullPath'], raiseWhenNotFound=True):
        ''' try to populate intance via LM API'''
        ''' searchOrder - controls what field and in what order use to search, when found other fileds will   be updated by data from LM
            raiseWhenNotFound if True will rise  LM_Session_Query_Error if group can't be found, if False just set data['LMSync_Timestamp'] to 0 and exit.
        '''
        if len(searchOrder) < 1 or len(searchOrder) > 2:
            raise lm_backend.LM_Session_Query_Error('Query error: searchOrder must contain between 1 to 2 entries', )
        for method in searchOrder:
            if method == 'id':
                result = self.LM_Session.get('/device/groups/' + str(self.data['id']))
                if result['status'] == 1069 and raiseWhenNotFound:
                    raise lm_backend.LM_Session_Query_Error('The hostgroup ID ' + str(self.data['id']) + ' is not found')
                    quit(1)
                elif result['status'] not in (200, 1069):
                    print(str(result))
                    raise lm_backend.LM_Session_Query_Error('Query error: ' + result['errmsg'])
                    quit(1)
                else:
                    self.__update_data__(result['data'])
                    self.data['Update_Timestamp'] = int(time.time())
                    self.data['LMSync_Timestamp'] = self.data['Update_Timestamp']
                    return
            if method == 'fullPath':
                result = self.LM_Session.get('/device/groups', params={'filter': 'fullPath:' + str(self.data['fullPath'])})
                # print(json.dumps(result, indent=4))
                if result['status'] != 200:
                    raise lm_backend.LM_Session_Query_Error('Query error' + result['errmsg'])
                    quit(1)
                if result['data']['total'] > 1:
                    raise lm_backend.LM_Session_Database_Error('LM API return more than 1 result in group search "' + self.data['fullPath'] + '"')
                    quit(1)
                elif result['data']['total'] == 0:
                    raise lm_backend.LM_Session_Database_Error('Device group "' + self.data['fullPath'] + '" was not found')
                    quit(1)
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
        ''' Creates group in LM, based on FullPath'''
        ''' Id field is ignored.
            if raiseIfExists is True and group already exist on same path then LM_Session_Query_Error will rised
            if raiseIfExists is False and group already exist on same path then set data['LMSync_Timestamp'] to 0 and exit
            If LM API returns an error exception will be always raised.
            After creation Read Only data get populated by second self.get() request
        '''

    def patch(self, raiseWhenNotFound=True):
        ''' Update exisiting LM Group by data from instance '''
        ''' Both Id and fullPath have to match data in LM, otherwise query will fail
        If LM API returns an error exception will be always raised.
        After succesful Read Only data get populated by second self.get() request
        '''
        pass

if __name__ == '__main__':
    quit()
