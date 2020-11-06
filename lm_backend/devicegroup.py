import time
import json

import lm_backend
import devicegroup


class DeviceGroup(devicegroup.DeviceGroup):

    def __init__(self, LM_Session, id=None, fullPath=None, deviceGroup=None):
        ''' can be created ether by specifying LM group ID or fullPath, or from base class'''
        # if not logicmonitor.LM_Session.is_dataclass(LM_Session):
        #    raise LM_Session_Error('LM_Session must be type of logicmonitor.LM_Session. got: ' + type(LM_Session))
        #    quit(1)
        if id is None and fullPath is None and deviceGroup is None:
            print(id, fullPath, deviceGroup)
            raise lm_backend.LM_Session_Error('ether id,filePath or deviceGroup need to be provided')
            quit(1)

        # know it is not a right way, but have no idea how to proprly poulate fields from nase class
        if deviceGroup is not None:
            if issubclass(deviceGroup.__class__, devicegroup.DeviceGroup):
                super(lm_backend.DeviceGroup, self).clone(deviceGroup)
            else:
                raise lm_backend.LM_Session_Error('"deviceGroup" bust be subclass of devicegroup.DeviceGroup. Got: ' + str(type(deviceGroup)))
        else:
            super(lm_backend.DeviceGroup, self).__init__()
            if id is not None:
                result = LM_Session.get('/device/groups/' + str(id))
                if result['status'] != 200:
                    raise lm_backend.LM_Session_Query_Error('Query error' + result['errmsg'])
                    quit(1)

            elif fullPath is not None:
                result = LM_Session.get('/device/groups', params={'filter': 'fullPath:' + str(fullPath)})
                # print(json.dumps(result, indent=4))
                if result['status'] != 200:
                    raise lm_backend.LM_Session_Query_Error('Query error' + result['errmsg'])
                    quit(1)
                if result['data']['total'] > 1:
                    raise lm_backend.LM_Session_Database_Error('LM API return more than 1 result in group search "' + fullPath + '"')
                    quit(1)
                elif result['data']['total'] == 0:
                    raise lm_backend.LM_Session_Database_Error('Device group "' + fullPath + '" was not found')
                    quit(1)
                else:
                    result['data'] = result['data']['items'][0]
            else:  # we already checked that some of paramiters are not none.
                raise lm_backend.LM_Session_Internal_Error("This should not happen ever")

            # copying of data from LM
            for key_id in result['data'].keys():
                if key_id in DeviceGroup.keys_to_store:
                    self.data[key_id] = result['data'][key_id]
            self.LMSync_Timestamp = int(time.time())

    def sync2LM(self):
        pass

    def sync2backend(self):
        pass

    def sync(self):
        ''' Sync to backend and LM '''
        self.sync2backend()
        self.sync2LM()


if __name__ == '__main__':
    quit()
