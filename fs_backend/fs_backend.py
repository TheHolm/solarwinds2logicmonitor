# pretty much placeholter


class FS_Session_Error(Exception):
    """Base class for other exceptions"""
    pass


class FS_Session_Database_Error(FS_Session_Error):
    """Raised when Logic Monitor API returns strange and unexpected data. Indicates problem with LM or in this module logic. Raise bug report or ticket with LM """
    pass


class FS_Session_Query_Error(FS_Session_Error):
    """Raised when Logic Monitor API returns error. Check your query data"""
    pass


class FS_Session_Internal_Error(FS_Session_Error):
    """Raised when something wrong with module itself. Raise a bug report"""
    pass


if __name__ == '__main__':
    quit()
