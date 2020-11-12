import pytest
import configparser
import json


def __copy_from_config_ini(config_section, keys_to_copy):
    config = configparser.ConfigParser(interpolation=None)
    config.read("config.ini")

    data = {}
    for key in keys_to_copy:
        data[key] = json.loads(config[config_section][key])
    return data


@pytest.fixture(scope="session")
def sandbox_login_details():
    ''' Coping data from INI file is intentially manual to avoid "silent" adding of paramiters. '''
    return __copy_from_config_ini('LogicMonitor', ('access_id', 'access_key', 'company'))


@pytest.fixture(scope="session")
def file_backend_details():
    return __copy_from_config_ini('FileTreeBackend', ('path', ))
