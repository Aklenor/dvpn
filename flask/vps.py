#/bin/env python

from configparser import ConfigParser
import yaml
from flask import request, jsonify, json
from threading import Thread
import urllib.request as UR
import ipaddress
import subprocess
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(SCRIPT_DIR+'/..')

inventory = {}
inventory.setdefault('all', {'children':
                                {'vps':
                                    {'hosts':
                                        {}
                                    }
                                }
                            })
VPS_dict = inventory['all']['children']['vps']['hosts']

fileInventory = work_dir+'/hosts.yml'
setupPlaybook = work_dir+'/roles/setup.yml'
deletePlaybook = work_dir+'/roles/delete.yml'

# read invtory file to global var: inventory
def read_inventory():
    global inventory
    global VPS_dict
    with open(fileInventory, 'r') as stream:
        try:
            inventory['all'] = yaml.safe_load(stream).get('all')
            # inventory = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print('Error while read inventory file\n',
                    exc)
            return 
    VPS_dict = inventory['all']['children']['vps']['hosts']

# set vars in inventory for vps group if they are not exists:
#   'host_id' for all hosts
#   'hostname' necessary to parce it in frontend
#   'interface' based on 'host_id'
#   'routes' as a list of dicts
def fix_inventory():
    global VPS_dict
    for hostname in VPS_dict: 
        # ID
        if VPS_dict[hostname].get('host_id') is None:
            VPS_dict[hostname]['host_id'] = getAvailableId()
        VPS_dict[hostname]['interface'] = 'tun'+str(VPS_dict[hostname].get('host_id'))
        # hostname
        if VPS_dict[hostname].get('hostname') is None:
            VPS_dict[hostname]['hostname'] = hostname

        # IP_info
        vps_ip_address = VPS_dict[hostname].get('ansible_host')
        VPS_dict[hostname]['ip_info'] = getIpLocation(vps_ip_address)

        # Routes
        if type(VPS_dict[hostname].get('routes')) is not list:
            VPS_dict[hostname]['routes'] = []
        uniq = []
        for route in VPS_dict[hostname].get('routes'):
            if (route not in uniq) and (route is not None):
                uniq.append(route)
        VPS_dict[hostname]['routes'] = uniq

    check_vps()
    write_inventory()

def write_inventory():
    with open(fileInventory, 'w') as stream:
        try:
            yaml.dump(inventory, stream, default_flow_style=False, allow_unicode=True)
        except yaml.YAMLError as exc:
            print('Error while write to inventory file',
                    exc)

def getAvailableId():
    global VPS_dict
    IDs = [VPS_dict[host].get('host_id') for host in VPS_dict]
    print('print IDs',IDs)
    findMinFreeElem = min( set(range(max(IDs)+2)) - set(IDs) )
    return findMinFreeElem

def getIpLocation(ip):
    # use ipinfo to get location of VPS server
    ip = str(ip)
    url = 'http://ipinfo.io/'+ip+'/json'

    try:
        response = UR.urlopen(url)
    except: 
        return {"status":"error", "message":"urllib.request.urlopen("+url+") catch exception"}

    data = json.load(response)
    if 'bogon' in data:
        return {"bogon":True}
    else:
        return {"bogon":False,
                "country": data.get('country'),
                "region": data.get('region'),
                "city": data.get('city')}

# form servers_list to send it to Front
# def get_vps_list():
#     # this variable in 'inventory file' will be used as VPS's IP address
#     # global inventory
#     addressParameter='ansible_host'
#     servers_dict = {}
#     for hostname in VPS_dict:
#         item = {}
#         item['hostname'] = hostname
#         item['ip'] =  VPS_dict[ hostname ].get( addressParameter )
#         item['ip_info'] = getIpLocation(VPS_dict[ hostname ].get( addressParameter ))
#         item['interface'] = VPS_dict[ hostname ].get('interface')
#         item['vpn_ip'] = '10.0.0.' + str(VPS_dict[ hostname ].get('host_id')*4+1)
#         item['routes'] = VPS_dict[hostname].get('routes')
#         item['state'] = VPS_dict[hostname].get('state')
#         item['configured'] = VPS_dict[hostname].get('configured')
#         servers_dict[ hostname ] = item
#     return servers_dict

def add_route( srcIP, destIP, hostname, description='' ):
    # global VPS_dict
    # print(srcIP, destIP, hostname)
    try: ipaddress.ip_network(srcIP)
    except ValueError:
        return jsonify({ 'status':'error', 'message': "'"+ srcIP + "' is bad source IP" }), 500
    try: ipaddress.ip_network(destIP)
    except ValueError:
        return jsonify({ 'status':'error', 'message': "'"+ destIP + "' is bad destination IP or subnet" }), 500
    if hostname not in VPS_dict:
        return jsonify({ 'status':'error', 'message': "\'" + hostname + "' is bad hostname" }), 500

    # IP RULE on IPCS
    # check if rule already exists
    ipRuleList = subprocess.run(['ip','rule','list','table','1'], 
                                capture_output=True, text=True).stdout
    # not quiet shure, maybe better to use regexp:
    if 'from '+ srcIP +' to '+ destIP not in ipRuleList:
        # add ip rule on IPCS
        cmdIpRuleAdd = ['sudo','ip','rule','add','from',srcIP,'to',destIP, 'table','1']
        resIpRuleAdd = subprocess.run(cmdIpRuleAdd, capture_output=True, text=True)
        # check for errors
        if resIpRuleAdd.returncode != 0:
            print('Error during run command:', ' '.join(cmdIpRuleAdd),
                    '\nRetrun Code: ', resIpRuleAdd.returncode,
                    '\nstdout: ', resIpRuleAdd.stdout,
                    '\nstderr: ', resIpRuleAdd.stderr)
    
    # IP ROUTE on IPCS
    # check if route already exists
    ipRouteList = subprocess.run(['ip','route','list','table','1'], 
                                capture_output=True, text=True).stdout

    interface = VPS_dict[hostname]['interface']
    # not quiet shure, maybe better to use regexp
    if destIP +' dev '+ interface not in ipRouteList:
        # add ip route on IPCS
        cmdIpRouteAdd = ['sudo','ip','route','add',destIP,'dev', interface, 'table','1']
        resIpRouteAdd = subprocess.run(cmdIpRouteAdd, capture_output=True, text=True)
        # check for errors
        if resIpRouteAdd.returncode != 0:
            print('Error during run command:', ' '.join(cmdIpRouteAdd),
                    '\nRetrun Code: ', resIpRouteAdd.returncode,
                    '\nstdout: ', resIpRouteAdd.stdout,
                    '\nstderr: ', resIpRouteAdd.stderr)

    # add route to inventory
    host_params = VPS_dict[hostname]
    route = {'route': description, 'source': srcIP, 'destination': destIP }
    # add 'routes' variable as list if not exists
    if type(host_params.get('routes')) is not list: 
        host_params['routes']=[route]
    else:
        host_params['routes'].append(route)

    # write new inventory to file
    # write_inventory()

    # IP ROUTE on VPS
    AnsibleExtraVars = json.dumps(host_params)
    cmdAnsible = ['ansible-playbook','-i',fileInventory,'--limit=' + str(hostname),'--tags=add_route',
            '--extra-vars', AnsibleExtraVars, setupPlaybook]
    resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

    if resAnsible.returncode != 0 :
        print('Error during run command:', ' '.join(cmdAnsible),
                    '\nRetrun Code: ', resAnsible.returncode,
                    '\nstdout: ', resAnsible.stdout,
                    '\nstderr: ', resAnsible.stderr)
        return jsonify({ 'status':'error', 
            'message': 'ansible-playbook return code: ' + str(resAnsible.returncode) }), 500
    else:
        write_inventory()
        return jsonify({'status':'ok', 'message':'route completed'}), 200

def check_vps( hostname='vps' ):
    # check for availability to work with ansible
    global VPS_dict
    cmdAnsible = ['ansible', hostname,'-i',fileInventory, '-m',
    'ping', '-o']
    resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)
    out = resAnsible.stdout.split('\n')
    out.remove('')
    for line in out:
        if ' |' not in line:
            VPS_dict[host]['state'] = "unreachable"
            continue
        host, status = line.split(' |')
        if 'SUCCESS' in status:
            VPS_dict[host]['state'] = "available"
        else:
            VPS_dict[host]['state'] = "unreachable"
    
# wrong function rewrite ConfigParser to yaml!!!
def add_vps( hostname, parameters ):
    # check if hostname is exists
    # VPS_dict = inventory['all']['children']['vps']['hosts']
    global VPS_dict

    if type(parameters) is not dict:
        return jsonify({"status":"error",
            "message":"parameters \'"+parameters+"\' is not a dictionary"}), 400

    if hostname in VPS_dict:
        return jsonify({"status":"error",
            "message":"host \'"+hostname+"\' already exists"}), 400

    id = getAvailableId()
    VPS_dict[hostname] = parameters
    VPS_dict[hostname]['host_id'] = id
    VPS_dict[hostname]['interface'] ='tun'+str(VPS_dict[hostname].get('host_id'))
    VPS_dict[hostname]['configured'] = 'no'
    VPS_dict[hostname]['routes'] = []
    write_inventory()

    check_vps(hostname)
    config_vps(hostname)
    
    return jsonify({"status":"ok","message":"new host added"}), 200

def del_vps( hostname ):
    global VPS_dict
    if hostname not in VPS_dict:
        return jsonify({"status":"error",
                        "message":"'" + hostname + "' no such host"}), 500
    check_vps(hostname)
    if VPS_dict[hostname]['state'] != 'available':
        VPS_dict.pop(hostname)
        return jsonify({'status':'ok', 'message':'VPS is removed'}), 200

    cmdAnsible = ['ansible-playbook','-i',fileInventory,'--limit=' + str(hostname),
                deletePlaybook]
    resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

    if resAnsible.returncode != 0 :
        print('Error during run command:', ' '.join(cmdAnsible),
                    '\nRetrun Code: ', resAnsible.returncode,
                    '\nstdout: ', resAnsible.stdout,
                    '\nstderr: ', resAnsible.stderr)
        return jsonify({ 'status':'error', 
            'message': 'ansible-playbook return code: ' + str(resAnsible.returncode) }), 500
    else:
        VPS_dict.pop(hostname)
        return jsonify({'status':'ok', 'message':'VPS is removed'}), 200

def edit_vps( hostname, parameters ):
    global VPS_dict
    # check if hostname is exists
    if hostname not in VPS_dict:
        return jsonify({"status":"error",
            "message":"host \'"+hostname+"\' don't exists"}), 400

    for parameter in parameters:
        VPS_dict[hostname][parameter] = parameters.get(parameter)
    write_inventory()
    check_vps(hostname)

    return jsonify({"status":"ok","message":"new host added"}), 200

# PROBLEM: keep system routes and routes in inventory synced


def config_vps(hostname='vps'):
    global VPS_dict
    
    def conf_one_vps( hostname ):
        hostname = str(hostname)
        global VPS_dict
        if hostname not in VPS_dict or not 'vps':
            print( "'" + hostname + "' no such host" )
            return {"status":"error",
                            "message":"'" + hostname + "' no such host"}

        if VPS_dict[hostname]['state'] != 'available':
            print( "'" + hostname + "' host is unreachable" )
            return {'status':'error', 'message':'VPS is unreachable'}

        VPS_dict[hostname]['configured'] = 'in progress'
        cmdAnsible = ['ansible-playbook','-i',fileInventory,'--limit=' + str(hostname),
                    setupPlaybook]
        resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

        if resAnsible.returncode != 0 :
            print('Error during run command:', ' '.join(cmdAnsible),
                  '\nRetrun Code: ',    resAnsible.returncode,
                  '\nstdout: ',         resAnsible.stdout,
                  '\nstderr: ',         resAnsible.stderr)
            return { 'status':'error', 
                'message': 'ansible-playbook return code: ' +
                str(resAnsible.returncode) }
        else:
            VPS_dict[hostname]['configured'] = 'yes'
            return {'status':'ok', 'message':'VPS is configured'}

    # TODO parse playbook output to change VPS_dict[hostname]['configured'] status
    def conf_all_vps():
        global VPS_dict
        # for hostname in VPS_dict:
        #     VPS_dict[hostname]['configured'] = "in progress"

        cmdAnsible = ['ansible-playbook','-i',fileInventory,
                    setupPlaybook]
        resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

        if resAnsible.returncode != 0 :
            print('Error during run command:', ' '.join(cmdAnsible),
                  '\nRetrun Code: ',    resAnsible.returncode,
                  '\nstdout: ',         resAnsible.stdout,
                  '\nstderr: ',         resAnsible.stderr)
            return { 'status':'error', 
                'message': 'ansible-playbook return code: ' +
                str(resAnsible.returncode) }
        else:
            return {'status':'ok', 'message':'VPS is configured'}

    if hostname == 'vps':
        confTread = Thread(target=conf_all_vps)
    else:
        confTread = Thread(target=configure_vps, args=(hostname,))

    confTread.start()
