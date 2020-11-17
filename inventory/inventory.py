class Inventory_Error(Exception):
    """Base class for other exceptions"""
    pass


class Inventory_Query_Error(Inventory_Error):
    """Raised when module can't complete request. Check your query data"""
    pass


class Inventory_Internal_Error(Inventory_Error):
    """Raised when something wrong with module itself. Raise a bug report"""
    pass


if __name__ == '__main__':
    quit()
