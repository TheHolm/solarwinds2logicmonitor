import lm_backend
# you will need your config.ini with UAT LM enviromet details to run these tests.


class Test_API_Session:
    def test__init__01(self, sandbox_login_details):
        ''' does not do much , just store Auth data in variables and tests that they a valig by getting some node data '''
        session = lm_backend.API_Session(sandbox_login_details['access_id'],
                                         sandbox_login_details['access_key'],
                                         sandbox_login_details['company'])
        assert 1

    def test__call_API__01(self):
        ''' Make a call to LM API endpoint returns json'''
        ''' payload, params - can be and should be a dicitionary '''
        pass

    def test_get_01(self, sandbox_login_details):
        ''' Simple wrper for call_API, saves you affor to passing GET to it'''
        session = lm_backend.API_Session(sandbox_login_details['access_id'],
                                         sandbox_login_details['access_key'],
                                         sandbox_login_details['company'])
        # group ID 1 always existis it is root folder.
        result = session.get('/device/groups/1', params='fields=displayName,id')
        assert result['status'] == 200

    def test_post_01(self):
        ''' Simple wrper for __call_API__, saves you affor to passing POST to it'''
        pass

    def test_patch_01(self):
        ''' Simple wrper for __call_API__, saves you affor to passing PATCH to it'''
        pass

    def test_delete_01(self):
        ''' Simple wrper for __call_API__, saves you affor to passing DELETE to it'''
        pass


if __name__ == '__main__':
    quit()
