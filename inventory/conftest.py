import pytest
import inventory


@pytest.fixture(scope="module")
def Inventory_Tree_Instance():
    ''' Coping data from INI file is intentially manual to avoid "silent" adding of paramiters. '''
    return inventory.Inventory_Tree()
