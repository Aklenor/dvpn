#/bin/env python

from configparser import ConfigParser
from flask import request, jsonify, json
import urllib.request as UR
import ipaddress
import subprocess
import os

servers_list = []
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
    ip = str(ip)
    url = 'http://ipinfo.io/'+ip+'/json'
    try:
        return json.load(UR.urlopen(url))
    except:
        return {"status":"error"}


# This function updates values in servers_list dictionary
def get_vps_list():
    addressParameter='ansible_ssh_host'
    servers = read_config()
    for hostname in servers:
        item = {}
        item['hostname'] = hostname
        item['ip'] =  servers[ hostname ].get( addressParameter )
        item['ip_info'] = getIpLocation(servers[ hostname ].get( addressParameter ))
        item['interface'] = 'tun' + str(servers[ hostname ].get('id'))
        item['vpn_ip'] = '10.0.0.' + str(servers[ hostname ].get('id')*4+1)
        servers_list.append(item)
    
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
