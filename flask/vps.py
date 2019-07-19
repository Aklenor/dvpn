#/bin/env python

from configparser import ConfigParser
import yaml
from flask import request, jsonify, json
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

def fix_inventory():
    global VPS_dict
    ID = 0
    for hostname in VPS_dict: 
        VPS_dict[hostname]['host_id'] = ID
        VPS_dict[hostname]['interface'] = 'tun'+str(ID)
        ID += 1

def write_inventory():
    with open(fileInventory, 'w') as stream:
        try:
            yaml.dump(inventory, stream, default_flow_style=False, allow_unicode=True)
        except yaml.YAMLError as exc:
            print('Error while write to inventory file',
                    exc)

def getIpLocation(ip):
    # use ipinfo to get location of VPS server
    ip = str(ip)
    url = 'http://ipinfo.io/'+ip+'/json'
    try:
        return json.load(UR.urlopen(url))
    except:
        return {"status":"error"}

# form servers_list to send it to Front
def get_vps_list():
    # this variable in 'inventory file' will be used as VPS's IP address
    global VPS_dict
    addressParameter='ansible_ssh_host'
    servers_dict = {}

    for hostname in VPS_dict:
        item = {}
        item['hostname'] = hostname
        item['ip'] =  VPS_dict[ hostname ].get( addressParameter )
        item['ip_info'] = getIpLocation(VPS_dict[ hostname ].get( addressParameter ))
        item['interface'] = 'tun' + VPS_dict[ hostname ].get('interface')
        item['vpn_ip'] = '10.0.0.' + str(VPS_dict[ hostname ].get('host_id')*4+1)
        item['routes'] = VPS_dict[hostname].get( 'routes' )
        servers_dict[ hostname ] = item
    return servers_dict

def add_route( srcIP, destIP, hostname, description='' ):
    global VPS_dict
    print(srcIP, destIP, hostname)
    if srcIP is None or destIP is None or hostname is None:
        return jsonify({ 'status':'error', 'message':'got null parameters check syntax' }), 500
    if hostname not in VPS_dict:
        return jsonify({ 'status':'error', 'message': '\'' + hostname + '\' is bad hostname' }), 500
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
    # not quiet shure, maybe better to use regexp
    if destIP +' dev '+ VPS_dict[hostname]['interface'] not in ipRouteList:
        # add ip route on IPCS
        cmdIpRouteAdd = ['sudo','ip','rule','add','from',srcIP,'to',destIP, 'table','1']
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
    if host_params.get('routes') is None: 
       host_params['routes']=[route]
    host_params['routes'].append(route)

    # write new inventory to file
    write_inventory()

    print(inventory)
    # IP ROUTE on VPS
    cmdAnsible = ['ansible-playbook','-i',fileInventory,'--limit=' + str(hostname),'--tags=add_route',
            setupPlaybook]
    resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

    if resAnsible.returncode != 0 :
        print('Error during run command:', ' '.join(cmdAnsible),
                    '\nRetrun Code: ', resAnsible.returncode,
                    '\nstdout: ', resAnsible.stdout,
                    '\nstderr: ', resAnsible.stderr)
        return jsonify({ 'status':'error', 
            'message': 'ansible-playbook return code: ' + str(resAnsible.returncode) }), 500
    else:
        VPS_dict[hostname]['routes'] = {'from':srcIP, 'to':destIP}
        return jsonify({'status':'ok', 'message':'route completed'}), 200

# wrong function rewrite ConfigParser to yaml!!!
def add_vps( hostname, parameters ):
    # check if hostname is exists
    # VPS_dict = inventory['all']['children']['vps']['hosts']
    global VPS_dict
    if hostname in VPS_dict:
        return jsonify({"status":"error",
            "message":"host \'"+hostname+"\' already exists"}), 400

    VPS_dict[hostname] = parameters
    VPS_dict[hostname]['host_id'] = len(VPS_dict)

    return jsonify({"status":"ok","message":"new host added"}), 200

    # print(hostname, parameters)
    # command = [ 'ansible-inventory', '-i', PathInvFileTmp,
    #             '--host='+hostname ]
    # rc = subprocess.call(command,cwd=work_dir,
    #         stderr=subprocess.DEVNULL,
    #         stdout=subprocess.DEVNULL)
    # print(rc)
    # if (rc != 0):
    #     os.remove(PathInvFileTmp)
    #     return jsonify({"status":"error","message":"wrong inventory parameters"})
    # else:
    #     os.rename(PathInvFileTmp, PathInvFile)
    #     return jsonify({"status":"ok","message":"new host added"}), 200
