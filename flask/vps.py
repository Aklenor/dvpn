#/bin/env python

from configparser import ConfigParser
from flask import request, jsonify, json
import urllib.request as UR
import ipaddress

servers_list = {}

def read_config():
    work_dir = '/home/berkut/projects/dvpn/'
    inventory_file = 'hosts'
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
    
def add_route( destination, vps ):
    try:
        dst = ipaddress.ip_address(destination)
    except ValueError:
        msg = '\'' + destination + '\' is Bad IP Address'
        return jsonify(status='error', message=msg ), 400
    if vps not in servers_list:
        msg = '\'' + vps + '\' is Bad VPS hostname'
        return jsonify(status='error', message=msg ), 400
    # TODO execute here ansible-playbook -l 
    print('from: {} to {} via {}'.format(request.remote_addr, dst, vps))
    return jsonify({'status':'ok', 'message':'route completed'}), 200
