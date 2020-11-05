import time
import json

import lm_backend
import devicegroup


class DeviceGroup(devicegroup.DeviceGroup):

    def __init__(self, LM_Session, id=None, fullPath=None):
        ''' can be created ether by specifying LM group ID or fullPath'''
        # if not logicmonitor.LM_Session.is_dataclass(LM_Session):
        #    raise LM_Session_Error('LM_Session must be type of logicmonitor.LM_Session. got: ' + type(LM_Session))
        #    quit(1)
        if id is None and fullPath is None:
            raise lm_backend.LM_Session_Error('ether id or filePath need to be provided')
            quit(1)

        super(lm_backend.DeviceGroup, self).__init__()
        result = LM_Session.get('/device/groups/' + str(id))
        if result['status'] != 200:
            raise lm_backend.LM_Session_Query_Error('Query error' + result['errmsg'])
            quit(1)
        else:
            for key_id in result['data'].keys():
                if key_id in DeviceGroup.keys_to_store:
                    self.data[key_id] = result['data'][key_id]
            self.LMSync_Timestamp = int(time.time())

        # now we got copy of data from LM


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
