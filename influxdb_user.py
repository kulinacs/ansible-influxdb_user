from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

try:
    from influxdb import InfluxDBClient
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False

from ansible.module_utils.basic import AnsibleModule

def connect(module):
    '''Connect to influxdb and return the client'''
    client = InfluxDBClient(
        host=module.params['hostname'],
        port=module.params['port'],
        username=module.params['user'],
        password=module.params['password'],
    )
    return client

def add_user(client, user, passwd, admin, check):
    '''Add a new user'''
    if not check:
        client.create_user(user, passwd, admin)

def del_user(client, user, check):
    '''Delete and existing user'''
    if not check:
        client.drop_user(user)
    
def make_admin(client, user, check):
    '''Make an existing user an admin'''
    if not check:
        client.grant_admin_privileges(user)

def set_pass(client, user, passwd, check):
    '''Set an existing users password'''
    if not check:
        client.set_user_password(user, passwd)
        
def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(required=True, type='str'),
            port=dict(default=8086, type='int'),
            authuser=dict(default='root', type='str'),
            authpass=dict(default='root', type='str', no_log=True),
            user=dict(required=True, type='str'),
            password=dict(required=True, type='str', no_log=True),
            state=dict(default='present', choices=['present', 'absent']),
            admin=dict(default=False, type='bool'),
            setpass=dict(default=False, type='bool')
        ),
        supports_check_mode=True
    )

    if not HAS_INFLUXDB:
        module.fail_json(msg='influxdb module must be installed')

    client = connect(module)

    # Gather current user state
    users = client.get_list_users()
    user_dict = [user for user in users if user['user'] == module.params['user']]
    if len(user_dict) == 1:
        user_dict = user_dict[0]
        user_admin = user_dict['admin']
    else:
        user_dict = None
        user_admin = None

    changed = False
    
    if module.params['state'] == 'present':
        if user_dict == None:
            changed = True
            add_user(client, module.params['user'], module.params['password'], module.params['admin'], module.check_mode)
        else:
            if user_admin != module.params['admin']:
                changed = True
                make_admin(client, module.params['user'], module.check_mode)
            if module.params['setpass']:
                changed = True
                set_pass(client, module.params['user'], module.params['password'], module.check_mode)
    else:
        if user_dict != None:
            changed = True
            del_user(client, module.params['user'], module.check_mode)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
