#!/bin/env python

from threading import Thread
import urllib.request as UR
import ipaddress
import subprocess
import os
from flask import jsonify, json
import yaml
import routed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.abspath(SCRIPT_DIR+'/..')

VPS_dict = {}

fileInventory = WORK_DIR+'/hosts.yml'
setupPlaybook = WORK_DIR+'/roles/setup.yml'
deletePlaybook = WORK_DIR+'/roles/delete.yml'

# read invtory file to global var: VPS_dict
def read_inventory():
    global VPS_dict
    with open(fileInventory, 'r') as stream:
        try:
            inventory = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print('Error while read inventory file\n',
                    exc)
            return
    VPS_dict = inventory['all']['children']['vps']['hosts']
    if VPS_dict == None:
        VPS_dict = {}

def write_inventory(fileInv=fileInventory, VPS_dict=VPS_dict):
    # global VPS_dict
    print(VPS_dict)
    inventory = {}
    inventory.setdefault('all', {'children':{'vps':{'hosts':{}}}})

    # TODO rid of unnecessary data in VPS_dict like:
    #    'hostname'

    inventory['all']['children']['vps']['hosts'] = VPS_dict

    with open(fileInv, 'w') as stream:
        try:
            yaml.dump(inventory, stream, default_flow_style=False, allow_unicode=True)
        except yaml.YAMLError as exc:
            print('Error while write to inventory file',
                  exc)

def getAvailableId():
    global VPS_dict

    IDs = []
    for host in VPS_dict:
        if VPS_dict[host].get('host_id') != None:
            IDs.append(VPS_dict[host].get('host_id'))

    if len(IDs) == 0:
        return 0
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

def route( action, srcIP, hostname, destIP='0.0.0.0/0', description='' ):
    global VPS_dict

    if type(hostname) is not str:
        return jsonify({ 'status':'error',
            'message': "requested 'hostname' is not string" }), 500

    if hostname not in VPS_dict:
        return jsonify({ 'status':'error',
            'message': "'" + hostname + "' is bad hostname" }), 400

    if type(srcIP) is not str or srcIP == '':

        return jsonify({ 'status':'error',
            'message': "requested source IP address is not string" }), 500

    try: ipaddress.ip_network(srcIP)
    except ValueError:
        return jsonify({ 'status':'error',
            'message': "'"+ srcIP + "' is bad source IP" }), 400

    if type(destIP) is not str or destIP == '':
        destIP = '0.0.0.0/0'

    try: ipaddress.ip_network(destIP)
    except ValueError:
        return jsonify({ 'status':'error',
            'message': "'"+ destIP + "' is bad destination IP or subnet" }), 400

    if destIP == '0.0.0.0/0':
        destIP = 'default'

    # check if action is valid
    if action not in ('add', 'delete'):
        return jsonify({ 'status':'error',
            'message': "'"+ str(action) + "' is bad action" }), 200

    routed.keepClean()

    interface = VPS_dict[hostname].get('interface')
    route = destIP+' dev '+interface
    # print('route:', route, 'interface:', interface)

    if action == 'add':
        actResult = routed.add2Ctable(srcIP,route)
    else:
        actResult = routed.del2Ctable(srcIP,route)

    message = actResult.get('message')

    if actResult.get('status') == 'ok':
        return jsonify({'status':'ok', 'message': message}), 200
    else:
        return jsonify({'status':'error', 'message': message}), 400

def check_vps(hostname, fileInventory=fileInventory, VPS_dict=VPS_dict):
    # check for availability to work with ansible

    # global VPS_dict

    cmdAnsible = ['ansible', hostname,'-i',fileInventory, '-m', 'ping', '-o']
    resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)
    message = ''.join([ 'during run command: ', ' '.join(cmdAnsible),
                        '\nRetrun Code: ', str(resAnsible.returncode),
                        '\nstdout: ', resAnsible.stdout,
                        '\nstderr: ', resAnsible.stderr ])

    if resAnsible.returncode != 0:
        VPS_dict[hostname]['state'] = "unreachable"
    else:
        VPS_dict[hostname]['state'] = "available"

def add_vps(hostname, parameters):
    # check if hostname is exists
    # VPS_dict = inventory['all']['children']['vps']['hosts']
    global VPS_dict

    if type(parameters) is not dict:
        return jsonify({"status":"error",
            "message":"parameters \'"+parameters+"\' is not a dictionary"}), 400

    if hostname in VPS_dict:
        return jsonify({"status":"error",
            "message":"host \'"+hostname+"\' already exists"}), 400

    def delEmptyParams(parameters):
        P = parameters.copy()
        for p in P:
            if P[p] == '':
                parameters.pop(p)
        parameters = P

    delEmptyParams(parameters)
    testVpsDict = {hostname:parameters}
    test_inventory=WORK_DIR+'/test.yml'
    write_inventory(test_inventory, testVpsDict)

    check_vps(hostname, test_inventory, testVpsDict)

    if testVpsDict[hostname].get('state') == 'unreachable':
        return jsonify({"status":"error",
            "message":"host seems unreachable for ansible"}), 400

    # id = getAvailableId()
    VPS_dict[hostname] = testVpsDict[hostname].copy()

    host_params = VPS_dict.get(hostname,{})
    host_params['host_id'] = getAvailableId()
    host_params['interface'] ='tun'+str(host_params.get('host_id'))
    host_params['hostname'] = hostname
    host_params['ip_info'] = getIpLocation(parameters['ansible_host'])
    host_params['configured'] = 'no'
    host_params['routes'] = []

    config_vps(hostname)
    write_inventory(VPS_dict=VPS_dict)
    return jsonify({"status":"ok", "message":"new host added"}), 200

def del_vps(hostname):
    global VPS_dict
    if hostname not in VPS_dict:
        return jsonify({"status":"error",
                        "message":"'" + str(hostname) + "' no such host"}), 400

    def execDel(hostname):
        hostname = str(hostname)
        global VPS_dict
        if hostname not in VPS_dict:
            print( "'" + hostname + "' no such host" )
            return {"status":"error",
                            "message":"'" + hostname + "' no such host"}

        if VPS_dict[hostname]['state'] != 'available':
            print( "'" + hostname + "' host is unreachable" )
            return {'status':'error', 'message':'VPS is unreachable'}

        VPS_dict[hostname]['configured'] = 'in deletion'
        cmdAnsible = ['ansible-playbook', '-i', fileInventory, '--limit', str(hostname),
                        deletePlaybook]
        resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

        if resAnsible.returncode != 0:
            print('Error during run command:', ' '.join(cmdAnsible),
                    '\nRetrun Code: ',    resAnsible.returncode,
                    '\nstdout: ',         resAnsible.stdout,
                    '\nstderr: ',         resAnsible.stderr)
            VPS_dict[hostname]['configured'] = 'deletion failed'
            write_inventory(VPS_dict=VPS_dict)
            return { 'status':'error',
                'message': 'ansible-playbook return code: ' +
                str(resAnsible.returncode) }
        else:
            VPS_dict.pop(hostname)
            write_inventory(VPS_dict=VPS_dict)
            return {'status':'ok', 'message':'VPS is removed'}

    deleteThread = Thread(target=execDel, args=(hostname,))
    deleteThread.start()
    return jsonify({'status':'ok', 'message':'VPS in removing process'}), 200

def config_vps(hostname='vps'):
    global VPS_dict

    def conf_one_vps( hostname ):
        hostname = str(hostname)
        global VPS_dict
        if hostname not in VPS_dict:
            print( "'" + hostname + "' no such host" )
            return {"status":"error",
                            "message":"'" + hostname + "' no such host"}

        if VPS_dict[hostname]['state'] != 'available':
            print( "'" + hostname + "' host is unreachable" )
            return {'status':'error', 'message':'VPS is unreachable'}

        VPS_dict[hostname]['configured'] = 'in progress'
        cmdAnsible = ['ansible-playbook', '-i', fileInventory, '--limit', str(hostname),
                      setupPlaybook]
        resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

        if resAnsible.returncode != 0:
            print('Error during run command:', ' '.join(cmdAnsible),
                  '\nRetrun Code: ',    resAnsible.returncode,
                  '\nstdout: ',         resAnsible.stdout,
                  '\nstderr: ',         resAnsible.stderr)
            VPS_dict[hostname]['configured'] = 'no'
            write_inventory(VPS_dict=VPS_dict)
            return { 'status':'error',
                'message': 'ansible-playbook return code: ' +
                str(resAnsible.returncode) }
        else:
            VPS_dict[hostname]['configured'] = 'yes'
            write_inventory(VPS_dict=VPS_dict)
            return {'status':'ok', 'message':'VPS is configured'}

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
        confTread = Thread(target=conf_one_vps, args=(hostname,))

    confTread.start()

def formRouteList():
    # TODO rename vars!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    routed.keepClean()
    Ctable = routed.Ctable
    print('Ctable', Ctable)
    inf2hn = {VPS_dict[hn].get('interface'):VPS_dict[hn] for hn in VPS_dict}

    clients = []
    for src, params in Ctable.items():
        routes = params.get('routes').values()
        R = {}
        R['source'] = src
        R['routes'] = []
        for route in routes:
            dst, _, interface, *_ = route.split()
            print('dst',dst,'interface',interface)
            r = {'VPS':inf2hn.get(interface),
                 'destination':dst}
            if r.get('VPS') == None:
                continue
            else:
                R['routes'].append(r)
        clients.append(R)

    return clients
