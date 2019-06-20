#!/usr/bin/env python

from backend import app

import os
import sys
import subprocess
# from ansible.parsing.dataloader import DataLoader
# from ansible.vars.manager import VariableManager
# from ansible.inventory.manager import InventoryManager
# from ansible.executor.playbook_executor import PlaybookExecutor


ansible_playbook = './playbooks/test.yml'

@app.route('/')
@app.route('/index')
def index():
    command = subprocess.Popen(['ansible-playbook',ansible_playbook],
                cwd='../',
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,) 
    stdout,stderr = command.communicate()
    command1 = subprocess.call("pwd")
    print(command1)
    print(stdout)
    print(stderr)

    # loader = DataLoader()

    # inventory = InventoryManager(loader=loader, sources='/home/demmy/Documents/RP2/dvpn/hosts')
    # variable_manager = VariableManager(loader=loader, inventory=inventory)
    # playbook_path = '/home/demmy/Documents/RP2/dvpn/playbooks/test.yml'

    # if not os.path.exists(playbook_path):
    #     print('[INFO] The playbook does not exist')
    #     sys.exit()

    # Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check','diff'])
    # options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=100, remote_user='slotlocker', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method='sudo', become_user='root', verbosity=None, check=False, diff=False)

    # variable_manager.extra_vars = {} # This can accomodate various other command line arguments.`

    # passwords = {}

    # pbex = PlaybookExecutor(playbooks=[playbook_path], inventory=inventory, variable_manager=variable_manager, loader=loader, passwords=passwords)

    # results = pbex.run()
    return stdout, stderr