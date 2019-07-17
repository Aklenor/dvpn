#/bin/env python

from configparser import ConfigParser
from flask import request, jsonify, json
import urllib.request as UR
import ipaddress
import subprocess
import os

servers_dict = {}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(SCRIPT_DIR+'/..')
Path2Inventory = work_dir+'/hosts'

# read invtory file and return dict
def read_config():
    inventory = ConfigParser(delimiters=' ')
    file = open(Path2Inventory,'r')
    inventory.read_file(file)
    file.close()

    VPS_dict = {}
    ID = 0
    for hostname, params_str in inventory.items('vps'):
        VPS_dict[ hostname ] = {}
        VPS_dict[ hostname ]['id'] = ID
        for params in params_str.split():
            key, value = params.split('=')
            VPS_dict[hostname][key]=value
        ID+=1
    return VPS_dict

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
    addressParameter='ansible_ssh_host'
    
    global servers_dict
    VPS_dict = read_config()
    for hostname in VPS_dict:
        item = {}
        item['hostname'] = hostname
        item['ip'] =  VPS_dict[ hostname ].get( addressParameter )
        item['ip_info'] = getIpLocation(VPS_dict[ hostname ].get( addressParameter ))
        item['interface'] = 'tun' + str(VPS_dict[ hostname ].get('id'))
        item['vpn_ip'] = '10.0.0.' + str(VPS_dict[ hostname ].get('id')*4+1)
        servers_dict[ hostname ] = item

def add_route( srcIP, destIP, hostname ):
    setRoutePlaybook = work_dir + '/roles/route.yml'

    try:
        ipaddress.ip_network(destIP)
    except ValueError:
        msg = '\'' + destIP + '\' is bad IP address'
        return jsonify(status='error', message=msg ), 400
    if hostname not in servers_list:
        msg = '\'' + str(hostname) + '\' is bad VPS hostname'
        return jsonify(status='error', message=msg ), 400

    print('from: {} to {} via {}'.format(srcIP , destIP,
        hostname))

    rc = subprocess.call(
                ['ansible-playbook', '-l ' + hostname,
                '-e', 'source=' + srcIP + ' destination=' + destIP,
                setRoutePlaybook],
            cwd=work_dir
            )

    if ( rc != 0 ):
        return jsonify({ 'status':'error', 'message':'ansible-playbook return code: '+str(rc) }), 500
    else:
        servers_dict[hostname]['routes'] = {'from':srcIP, 'to':destIP}
        return jsonify({'status':'ok', 'message':'route completed'}), 200

def add_vps( hostname, parameters ):

    PathInvFile = work_dir + inventory_file
    PathInvFileTmp = work_dir + inventory_file + '.test'
    
    InvFile = open( PathInvFile, 'r')
    InvFileTmp = open(PathInvFileTmp, 'w')

    inventory = ConfigParser(delimiters=' ')
    inventory.read_file(InvFile)
    InvFile.close()

    inventory.set('vps', hostname, parameters )
    inventory.write(InvFileTmp)
    InvFileTmp.close()

    command = [ 'ansible-inventory', '-i', PathInvFileTmp,
                '--host='+hostname ]
    rc = subprocess.call(command,cwd=work_dir,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL)
    print(rc)
    if (rc != 0):
        os.remove(PathInvFileTmp)
        return jsonify({"status":"error","message":"wrong inventory parameters"})
    else:
        os.rename(PathInvFileTmp, PathInvFile)
        return jsonify({"status":"ok","message":"new host added"}), 200
