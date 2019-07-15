# -*- coding: utf-8 -*-
from flask import render_template, request
from front_flask import app
import sys
import os
from ansib.ansib import ResultCallback


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)


def get_ping_status(result):
    for play in result:
        if "cmd" in play:
            # print(play["stdout"])
            try:
                return play["stdout"].split("min/avg/max/mdev = ")[1].split("/")[1]
            except IndexError:
                pass
    return "No ping"


def get_ansible_status(result):
    for play in result:
        if "unreachable" in play:
            return {"bad": True}
        elif "ping" in play:
            if play['_ansible_parsed']:
                return {"good": True}
            else:
                return {"not_good": True}
    return {"bad": None}


def get_end_timestamp(result):
    ret = "No contact"
    for play in result:
        # print(play)
        if 'end' in play:
            ret = play['end']
    return ret


@app.route('/')
@app.route('/index')
def index():
    ansible_playbook = '../roles/ovpn_server/tests/test.yml'

    if not os.path.isfile(ansible_playbook):
        print('[INFO] The playbook does not exist')
        sys.exit()

    rc = ResultCallback()
    rc.use_pb(ansible_playbook)

    # Instantiate our ResultCallback for handling results as they come in.
    # Ansible expects this to be one of its main display outlets
    pb_results = rc.result_for_flask
    # for host, res in pb_results.items():
    #     print(host)
    #     for play in res:
    #         print(play)

    results = list()
    results.append({"name": "hostname", "port": "VPN port", "ip": "VPS IP address",
                    "ping": "ping latency",
                    "ansible_status": {"not_good": True},
                    "vpn_status": "VPN status",
                    "time_check": "Contact timestamp"})
    for host in pb_results:
        results.append({"name": host, "port": "INSERT_PORT", "ip": "INSERT_IP_HERE",
                        "ping": get_ping_status(pb_results[host]),
                        "ansible_status": get_ansible_status(pb_results[host]),
                        "vpn_status": "",
                        "time_check": get_end_timestamp(pb_results[host])})
    return render_template('index.html', results=results)


@app.route('/index/USETHIS', methods=['GET', 'POST'])
def index_button():
    ansible_playbook = '../roles/ovpn_server/playbook_to_reroute.yml'

    if not os.path.isfile(ansible_playbook):
        print('[INFO] The playbook does not exist')
        sys.exit()

    rc = ResultCallback()
    # rc.use_pb(ansible_playbook, single_host=hostname)
    results = rc.result_for_flask
    return render_template('template_to_reroute.html', results=results)


@app.route('/list_of_vps')
def list_of_vps():
    rc = ResultCallback()
    list_of_vps = rc.get_list_of_hosts()
    return render_template('vps_test.html', list_of_vps=list_of_vps)


@app.route('/list_of_vps/<hostname>')
def vps_status(hostname):
    ansible_playbook = '../roles/ovpn_server/tests/test.yml'

    if not os.path.isfile(ansible_playbook):
        print('[INFO] The playbook does not exist')
        sys.exit()

    rc = ResultCallback()
    rc.use_pb(ansible_playbook, single_host=hostname)

    # Instantiate our ResultCallback for handling results as they come in.
    # Ansible expects this to be one of its main display outlets

    results = rc.result_for_flask
    # print(results)

    return render_template('single_vps.html', results=results)


@app.route('/list_of_vps/get_vps_<hostname>', methods=['GET', 'POST'])
def get_vps(hostname):
    # hostname=request.args.get('hostname')
    return vps_status(hostname)
