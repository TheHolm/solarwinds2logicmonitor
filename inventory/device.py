import time
import json

import inventory


class Device_Error(inventory.Inventory_Error):
    """Base class for other exceptions"""
    pass


class Device:
    ''' represent single device in LM or folder on disk, skeleton type got extened in "backend" modules '''
    class_keys = {  # Within LM some keys are stored in customProperties dictionary. But it bellow list of propeties wich should be stored in 'data' dictionary (and probaly requre some special handlig ). Evrything not listed there stored in 'extra' dict. Classes extending this class can add more fields to 'data'
                     # TODO  It different logic grom DeviceGroup and need to be implemented there to
                     'id': lambda arg: arg is None or arg > 0,
                     'hostGroupIds': lambda arg: type(arg) == list and all((isinstance(n, int) and n > 0) for n in arg),  # This is a LIST !!!
                     'description': lambda arg: arg is None or type(arg) == str,
                     'displayName': lambda arg: arg is None or type(arg) == str,
                     'name': lambda arg: arg is None or type(arg) == str,
                     }
    # it seem's it is easy to achive perls lever of ureadability in python

    def __init__(self, id=None, name='', hostGroups=[], data={}):
        '''  Just populate file structure. id and fullPath has priority over values in data'''
        ''' hostGroups is list of inventory.DeviceGroup objects device belongs to. First entry will become a primary group for device. '''
        # Init vars
        self.data = {}
        self.extra = {}
        for key_id in Device.class_keys.keys():
            self.data[key_id] = None
        self.data['hostGroupIds'] = []

        for key_id in data.keys():
            if key_id in Device.class_keys.keys():
                self.data[key_id] = data[key_id]
            else:
                self.extra[key_id] = data[key_id]

        if id is not None:
            self.data['id'] = id
        elif len(hostGroups) > 0 and name != '':
            self.data['name'] = str(name)
            for group in hostGroups:
                if group.data['id'] is not None:  # ToDo preaby need to check that group is appropriate type.
                    self.data['hostGroupIds'].append(group.data['id'])
                else:
                    raise Device_Error('"hostGroups" containse DeviceGrop with undefined Id')
                    quit(1)
        else:
            raise Device_Error('"Id" or "name" + "hostGroups" must be provided as paramiters')
            quit(1)

        # let's check results
        if not self.check_constrains():
            # only checking keys wich present in both dictionaries, just run checks functions defined in
            raise Device_Error('Constrains chack failed for ' + str(key_id))
            quit(1)

        self.data['LMSync_Timestamp'] = 0
        self.data['FSSync_Timestamp'] = 0
        self.data['Update_Timestamp'] = int(time.time())

    def check_constrains(self):
        ''' Checking data fieds in data to comply wit constrainse defined by lambda functions in Devices.class_keys '''
        class_data = self.__class__.class_keys  # this will work with choled classes to.
        return all(class_data[key_id](self.data[key_id]) for key_id in (set(self.data.keys()) & set(class_data.keys())))

    def clone(self, source):
        '''just copied data to self from other instance of same class'''
        # should I use deep copy instaed?
        if issubclass(source.__class__, inventory.Device):
            self.data = source.data
            self.extra = source.extra
        else:
            raise Device_Error('Expected subclass of <class DeviceGroup>, got {}.'.format(type(source)))

    def __str__(self):
        ''' human readable serialiation '''
        __header_l1__ = "Data was synced with LM: " + ('Never' if self.data['LMSync_Timestamp'] == 0 else (str(time.time() - self.data['LMSync_Timestamp']) + ' seconds ago')) + "\n"
        __header_l2__ = "Data was synced with file system backend: " + ('Never' if self.data['FSSync_Timestamp'] == 0 else (str(time.time() - self.data['FSSync_Timestamp']) + ' seconds ago')) + "\n"
        return(__header_l1__ + __header_l2__ + 'Data:\n' + json.dumps(self.data, indent=4) + '\nExtra:\n' + json.dumps(self.extra, indent=4))

    def __eq__(self, other):
        ''' Not implemented '''
        return (self.data == other.data)  # we do not care about extra, lets child classes care about it.



if __name__ == '__main__':
    quit()
