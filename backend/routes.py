# -*- coding: utf-8 -*-
from flask import render_template
from backend import app
import subprocess
import sys
import os
import json
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase

from collections import namedtuple


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)


class SampleCallback(CallbackBase):
    """Sample callback"""

    def __init__(self):
        super(SampleCallback, self).__init__()
        # store all results
        self.results = []

    def v2_runner_on_ok(self, result, **kwargs):
        """Save result instead of printing it"""
        self.results.append(result)


@app.route('/')
@app.route('/index')
def index():
    list_of_vps = [
        {
            'ip': "ip_address",
            'ping_status': {"online": "% of loss", "latency": "avg_latency"},
            'ansible_status': "ansible config enabled?",
            'vpn_status': "systemctl status ovpn"
        },
        {
            'ip': "127.0.0.1",
            'ping_status': {"online": "50", "latency": "100500"},
            'ansible_status': "failed",
            'vpn_status': "service could not be found"
        },
        {
            'ip': "localhost",
            'ping_status': {"online": "50", "latency": "100500"},
            'ansible_status': "failed",
            'vpn_status': "service could not be found"
        },
        {
            'ip': "8.8.8.8",
            'ping_status': {"online": "10", "latency": "100"},
            'ansible_status': "online",
            'vpn_status': "loaded/active"
        }
    ]
    return render_template('index.html', list_of_vps=list_of_vps)


@app.route('/ansible')
def ansible():
    ansible_playbook = '../roles/ovpn_server/tests/test.yml'
    # command = subprocess.Popen(['ansible-playbook', ansible_playbook],
    #                            cwd='../', stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    #                            universal_newlines=True,)
    # stdout, stderr = command.communicate()
    # command1 = subprocess.call("pwd")
    # print(command1)    # print(stdout)    # print(stderr)
    Options = namedtuple('Options',
                         ['connection', 'module_path', 'forks', 'become', 'become_method', 'become_user', 'check',
                          'diff', 'listhosts', 'listtasks', 'listtags', 'syntax'])
    loader = DataLoader()
    options = Options(connection='local', module_path='%s/' % (ROOT_DIR), forks=100, become=None, become_method=None,
                      become_user=None, check=False,
                      diff=False, listhosts=True, listtasks=False, listtags=False, syntax=False)

    inventory = InventoryManager(loader=loader, sources='../hosts')
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    if not os.path.isfile(ansible_playbook):
        print('[INFO] The playbook does not exist')
        sys.exit()

    # This can accomodate various other command line arguments
    # variable_manager.extra_vars = {}
    passwords = {}

    pbex = PlaybookExecutor(playbooks=[ansible_playbook], inventory=inventory,
                            variable_manager=variable_manager, options=options,
                            loader=loader, passwords=passwords)
    callback = SampleCallback()
    pbex._tqm._stdout_callback = callback

    return_code = pbex.run()
    results = callback.results

    # results = pbex.run()
    # results = json.dumps(results)
    return render_template('vps_test.html', results=results)  # , stdout=stdout, stderr=stderr)
