import sqlite3  # used mostly to speedup searches and introduce more bugs

import devicegroup
import inventory


class Inventory_Tree:

    def __init__(self):
        ''' Just init in-memory database and some variables.'''
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row

        # lets init groups tables.
        c = self.db.cursor()
        c.execute('PRAGMA foreign_keys = ON')

        '''  Table "groups" lists all device groups.
         key - in DB id. It is local for DB and only stored in memory.
         id  - External group id - corresponds to on disk oor Logic monitor ids. Not same as key.
         parentKey - in DB key of parrent group. NULL for root group.
         parentID - External parent group id.
         name TEXT - Just group name - mandatory
         fullPath TEXT - full path = path from root folder + name '''
        c.execute('''CREATE TABLE groups
                     (key INTEGER PRIMARY KEY,
                      id INT CHECK ( id > 0 or id IS NULL ),
                      parentKey INT REFERENCES groups(key),
                      parentId INT,
                      name TEXT ,
                      fullPath TEXT CHECK (  NOT ( fullPath IS NULL AND name IS NULL )  ) )''')
        c.execute('CREATE UNIQUE INDEX IDX_groups_id ON groups (id)')
        c.execute('CREATE INDEX IDX_groups_parentKey ON groups (parentKey)')

        '''  Table "domain" store list of IP domaind ( VRFs ), each VRF should have LM collectors group assosiated with it.
         key - in DB id. It is local for DB and only stored in memory.
         id  - External device id - corresponds collectors group Logic monitor ids. Not same as key.
         name TEXT - Just VRF like name  - optional (VRF name is usualy stored there.)
        '''
        c.execute('''CREATE TABLE domain
             (key INTEGER PRIMARY KEY,
              name TEXT NOT NULL CHECK name <> "",
              id INT CHECK ( id > 0 or id IS NULL )
              )
              ''')
        c.execute('CREATE UNIQUE INDEX IDX_domain_id ON domain (id)')

        ''' key - in DB id. It is local for DB and only stored in memory.
         id  - External device id - corresponds to on disk oor Logic monitor ids. Not same as key.
         parentKey - in DB key of parrent group. Foragin key, it must to be present in "groups" table.
         name TEXT - Just device name - mandatory
         URL TEXT - Examples: "snmp://1.1.1.1", "snmp://1.1.1.1:16161" and etc. HOw to monitor device. One mode per device.
         address_scope  - id of addres_scope where IP is belongs to (think VRF). Used to set LM Collectors Group and check for dublicate IPs. '''
        c.execute('''CREATE TABLE devices
                     (key INTEGER PRIMARY KEY,
                      id INT CHECK ( id > 0 or id IS NULL ),
                      parentKey INT NOT NULL REFERENCES groups(key),
                      name TEXT NOT NULL,
                      URL TEXT DEFAULT "none://127.0.0.1",
                      domain INT NOT NULL REFERENCES domain(key))
                      ''')
        c.execute('CREATE UNIQUE INDEX IDX_devices_id ON devices (id)')
        c.execute('CREATE UNIQUE INDEX IDX_devices_URL_domain ON devices (URL,domain)')
        self.db.commit()
        c.close()
        # Actuall device/group/domain objects are going to be stored in list bellow indexed by "key" in corresponding tables.
        # Not most effective way in terms of memory, but should be fastest to access.
        self.tree = []
        self.domains = []
        self.devices = []

    def add_group(self, device_group, doNotUpdate=False):
        '''Add a group database of type device.DeviceGroup, code will try it best to find parrents '''
        # fullpath - will extract group name ant try to find parrent based on rest of the path
        # Name + parentID. if parentID == -1  than parent is root.
        # doNotUpdate conrols should method add missing data to "device_group" based on data in database.
        # Any conflict between data in device_group and database will raise an exception

        if not issubclass(device_group.__class__, devicegroup.DeviceGroup):
            raise inventory.Inventory_Query_Error('device_grop must be sublass of devicegroup.DeviceGroup. Got ' + str(type(device_group)))
            quit(1)
        # All fields we need MUST be in devace_group data, they are initlased as part of devicegroup constructor.
        g_fullPath = device_group.data['fullPath'] if device_group.data['fullPath'] != '' else None
        g_name = device_group.data['name'] if device_group.data['name'] != '' else None

        # DB conflict check. It should not be other group with same id
        if device_group.data['id'] is not None:
            c = self.db.cursor()
            c.execute('SELECT id FROM groups WHERE id = ?', (device_group.data['id'], ))
            if c.fetchone() is not None:
                raise inventory.Inventory_Query_Error('device_group with Id  (' + str(device_group.data['id']) + ' alredy exist in database')
                quit(1)
            c.close()

        if g_fullPath not in (None, ''):

            path_list = g_fullPath.split('/')
            name_from_path = path_list[-1]
            if name_from_path == '':
                raise inventory.Inventory_Query_Error('device_group.fullPath can\'t ends with "/"')
                quit(1)
            if g_name in (None, '') and not doNotUpdate:
                device_group.data['name'] = name_from_path
                g_name = name_from_path
            elif g_name not in (None, name_from_path):
                raise inventory.Inventory_Query_Error('device_group.name (' + str(g_name) + ' does not match'
                                                      + 'name derived from device_group.fullPath (' + str(g_fullPath) + ')')
                quit(1)
            if len(path_list) == 1:
                # parent is root.
                parentKey = None
                parentId = None
            else:
                # let's try to find parent based on fullPath
                parentId = None
                parent_path = '/'.join(path_list[:-1])
                c = self.db.cursor()
                c.execute('SELECT key,id FROM groups WHERE fullPath = ? ', (parent_path,))
                results = c.fetchall()  # rowcount() is not fun to use
                if len(results) < 1:
                    # parent not found
                    raise inventory.Inventory_Query_Error('Parent of device_group.name (' + g_fullPath + ') was not found in database')
                    quit(1)
                elif len(results) > 1:
                    # multiple parents found - it seems to be database corruption
                    raise inventory.Inventory_Internal_Error('fullPath search of parent returned multiple values. It should not be possible')
                    quit(1)
                else:
                    # it should be only 1, I hope len() only returns int.
                    parentKey = results[0]['key']
                    parentId = results[0]['id']
                    # sanity check
                    if device_group.data['parentId'] not in (None, parentId):
                        raise inventory.Inventory_Query_Error('Value off device_group.parentId (' + str(device_group.data['parentId']) + ') does not match value in database (' + str(parentId))
                        quit(1)
                    elif not doNotUpdate:
                        device_group.data['parentId'] = parentId
                    else:
                        parentId = device_group.data['parentId']

        # fullPath is not defined. Let's try to add group based on parentId and name
        elif device_group.data['name'] in ('', None) or device_group.data['parentId'] is None:
            raise inventory.Inventory_Query_Error('Not enogh info in device_group to find group parent, ether fullPath ot name + parentID need tobe defined')
            quit(1)
        else:
            # let's find parent.
            if device_group.data['parentId'] == -1:  # no need to sarch for parent it is a root.
                parentKey = None
                parentId = -1
                g_fullPath = device_group.data['name']
            else:
                c = self.db.cursor()
                c.execute('SELECT key,fullPath FROM groups WHERE id = ? ', (device_group.data['parentId'],))
                results = c.fetchall()
                if len(results) < 1:
                    # parent not found
                    raise inventory.Inventory_Query_Error('ParentId of device_group.name (' + str(device_group.data['parentId']) + ') was not found in database')
                    quit(1)
                elif len(results) > 1:
                    # multiple parents found - it seems to be database corruption
                    raise inventory.Inventory_Internal_Error('fullPath search of parent returned multiple values. It should not be possible')
                    quit(1)
                else:
                    parentKey = results[0]['key']
                    parentId = device_group.data['parentId']
                    g_fullPath = results[0]['fullPath'] + "/" + device_group.data['name']

            if not doNotUpdate:
                device_group.data['fullPath'] = g_fullPath

        # checking for fullPath collisions
        c = self.db.cursor()
        c.execute('SELECT fullPath FROM groups WHERE fullPath = ?', (device_group.data['fullPath'], ))
        if c.fetchone() is not None:
            raise inventory.Inventory_Query_Error('device_group with fullPath (' + str(device_group.data['fullPath']) + ' alredy exist in database')
            quit(1)
        c.close()

        c = self.db.cursor()
        c.execute('INSERT INTO groups (id,parentKey, parentId, name, fullPath ) VALUES (?, ? , ? , ? , ? ) ',
                  (device_group.data['id'], parentKey, parentId, g_name, g_fullPath))
        self.tree.insert(c.lastrowid, device_group)
        c.close()

    def get_group(self, fullPath, ):
        ''' returns devicegroup instance, if it can find it'''
        pass

    def del_group(self):
        pass

    def update_group(self):
        '''mostly to move group under differnt parent'''
        pass

    def _check_db_integrity_(self):
        ''' Just to be realy caution, check DB for possible mistmatches '''

    def __str__(self):
        c = self.db.cursor()
        c.execute('SELECT * FROM groups')
        results = c.fetchone()
        ret = str(results.keys()) if len(results) > 0 else ''
        ret = "DB dump:\n" + ret + "\n"
        c.execute('SELECT * FROM groups')
        for r in c.fetchall():
            ret = ret + str(tuple(r)) + "\n"
        ret = ret + "\n" + str(self.tree)
        return (ret)


# lets test retrival
'''['key', 'id', 'parentKey', 'parentId', 'name', 'fullPath']
(1, 1000, -1, None, 'Customers', 'Customers')
(2, 2000, 1, 1000, 'Horns and Hooves', 'Customers/Horns and Hooves')
(3, None, 1, None, None, 'Customers/Horns and Hooves 2')
(4, 1001, -1, -1, 'Users', 'Users')
(5, None, 4, 1001, 'Jonh Smith', 'Users/Jonh Smith')
(6, None, 4, 1001, 'Jonh Carpenter', 'Users/Jonh Carpenter')
'''
