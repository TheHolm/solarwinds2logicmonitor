import pytest
import inventory
import devicegroup


class Test_Inventory_Tree:

    def test__init__01(self):
        ''' just check that init can run'''
        inventory.Inventory_Tree()

    # testing fullPAth based adds
    # DB state after running all sucsesull adds. It is not a good aproach as you can't run just single test realbely.
    # root - (1, 1000, -1, None, 'Customers', 'Customers')
    #               *-- (2, 2000, 1, 1000, 'Horns and Hooves', 'Customers/Horns and Hooves')
    #               * -- (2, 2000, 1, 1000, 'Horns and Hooves', 'Customers/Horns and Hooves')

    def test_add_group_01(self, Inventory_Tree_Instance):
        ''' Adding root group by full path'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 1000,
          "name": "Customers",
          "fullPath": "Customers",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0)
        print(it, g0)

    def test_add_group_02(self, Inventory_Tree_Instance):
        ''' fail if fullPath ended on /'''
        it = Inventory_Tree_Instance
        groupdata = {
          "name": "NoGroup",
          "fullPath": "NoGroup/",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_04(self, Inventory_Tree_Instance):
        ''' fail if name fullpPath mismatch '''
        it = Inventory_Tree_Instance
        groupdata = {
            "name": "Hooves and Horns",
            "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_03(self, Inventory_Tree_Instance):
        ''' fail when no parent can be found '''
        it = Inventory_Tree_Instance
        groupdata = {
          "name": "Horns and Hooves",
          "fullPath": "NoGroup/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_07(self, Inventory_Tree_Instance):
        ''' fail when parentId missmach '''
        it = Inventory_Tree_Instance
        groupdata = {
          "parentId": 1234,
          "name": "Horns and Hooves",
          "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_05(self, Inventory_Tree_Instance):
        ''' succesful add of child group with updates'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 2000,
          "name": None,
          "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0)  # should fail as no parent yet.
        assert g0.data['parentId'] == 1000
        assert g0.data['name'] == 'Horns and Hooves'
        print(it, g0)

    def test_add_group_06(self, Inventory_Tree_Instance):
        ''' succesful add of child group without updates'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": None,
          "fullPath": "Customers/Horns and Hooves 2",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0, doNotUpdate=True)  # should fail as no parent yet.
        assert g0.data['parentId'] is None
        assert g0.data['name'] is None
        print(it, g0)

    def test_add_group_08(self, Inventory_Tree_Instance):
        ''' fail tryinf to add group with same iD '''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 2000,
          "name": None,
          "fullPath": "Customers/Horns and Hooves 3",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_09(self, Inventory_Tree_Instance):
        ''' fail tryinf to add group with same path '''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": None,
          "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

# let test adding without fullPath
    def test_add_group_10(self, Inventory_Tree_Instance):
        ''' Adding root group by name and parentId'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 1001,
          "name": "Users",
          "parentId": -1
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0)
        assert g0.data['fullPath'] == "Users"
        print(it, g0)

    def test_add_group_15(self, Inventory_Tree_Instance):
        ''' fail trying to add root group with same name'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 1003,
          "name": "Users",
          "parentId": -1
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_11(self, Inventory_Tree_Instance):
        ''' Adding sub group by name and parentId'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": "Jonh Smith",
          "parentId": 1001
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0)
        assert g0.data['fullPath'] == "Users/Jonh Smith"
        assert g0.data['parentId'] == 1001
        print(it, g0)

    def test_add_group_12(self, Inventory_Tree_Instance):
        ''' Adding sub group by name and parentId, no updates'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": "Jonh Carpenter",
          "parentId": 1001
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0, doNotUpdate=True)
        assert g0.data['fullPath'] is None
        print(it, g0)

    def test_add_group_13(self, Inventory_Tree_Instance):
        ''' fail trying to add sub group by name and non exisiting parentId '''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": "Just Jonh",
          "parentId": 1002
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_14(self, Inventory_Tree_Instance):
        ''' fail trying to add sub group with same name and parentId '''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": "Jonh Smith",
          "parentId": 1001
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)
