#/bin/env python

from configparser import ConfigParser
from flask import request, jsonify, json
import urllib.request as UR
import ipaddress
import subprocess
import os

servers_list = {}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(SCRIPT_DIR+'/..')
inventory_file = '/hosts'

def read_config():
    inventory = ConfigParser(delimiters=' ')
    inventory.read_file(open(work_dir+inventory_file,'r'))
    servers = {}
    ID = 0

    for hostname, params_str in inventory.items('vps'):
        servers[ hostname ] = {}
        servers[ hostname ]['id'] = ID
        for params in params_str.split():
            key, value = params.split('=')
            servers[hostname][key]=value
        ID+=1
    return servers

def getIpLocation(ip):
    url = 'http://ipinfo.io/'+ip+'/json'
    return json.load(UR.urlopen(url))

# This function updates values in servers_list dictionary
def get_vps_list():
    addressParameter='ansible_ssh_host'
    servers = read_config()
    for hostname in servers:
        servers_list[ hostname ] = {}
        servers_list[ hostname ]['ip'] =  servers[ hostname ][ addressParameter ]
        servers_list[ hostname ]['ip_info'] = getIpLocation(servers[ hostname ][ addressParameter ])
        servers_list[ hostname ]['interface'] = 'tun' + str(servers[ hostname ]['id'])
        servers_list[ hostname ]['vpn_ip'] = '10.0.0.' + str(servers[ hostname ]['id']*4+1)
    
def add_route( srcIP, destIP, hostname ):
    changeRoutePlaybook = 'roles/route.yml'
    try:
        ipaddress.ip_address(destIP)
    except ValueError:
        msg = '\'' + destIP + '\' is Bad IP Address'
        return jsonify(status='error', message=msg ), 400
    if hostname not in servers_list:
        msg = '\'' + str(hostname) + '\' is Bad VPS hostname'
        return jsonify(status='error', message=msg ), 400

    print('from: {} to {} via {}'.format(srcIP , destIP,
        hostname))

    rc = subprocess.call(
            ['ansible-playbook', '-l ' + hostname,
            '-e', 'source=' + srcIP + ' destination=' + destIP,
            changeRoutePlaybook],
            cwd=work_dir
            )

    if ( rc != 0 ):
        return jsonify({ 'status':'error', 'message':'ansible-playbook return code: '+str(rc) }), 500
    else:
        return jsonify({'status':'ok', 'message':'route completed'}), 200

def add_vps( hostname, parameters ):
    InvFile = open(work_dir + inventory_file, 'r')
    newInvFile = open(work_dir + inventory_file + 'test', 'w')
    inventory = ConfigParser(delimiters=' ')
    inventory.read_file(InvFile)
    InvFile.close()
    inventory.set('vps', hostname, parameters )
    inventory.write(newInvFile)
    newInvFile.close()

