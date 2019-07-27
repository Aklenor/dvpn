#/bin/env python

from configparser import ConfigParser
import yaml
from flask import request, jsonify, json
from threading import Thread
import urllib.request as UR
import ipaddress
import subprocess
import os
import routed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(SCRIPT_DIR+'/..')

VPS_dict = {}

fileInventory = work_dir+'/hosts.yml'
setupPlaybook = work_dir+'/roles/setup.yml'
deletePlaybook = work_dir+'/roles/delete.yml'

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
    return VPS_dict

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

    IDs = [VPS_dict[host].get('host_id') for host in VPS_dict]
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

    # add route back on VPS
    def setVpsRoute( hostname, source, action ):

        # get copy of VPS variables
        host_params = VPS_dict.get(hostname).copy()
        host_params['routes'] = [ {'source':source} ]

        if action == 'add':
            ansibleTags = 'add_route'
        else:
            ansibleTags = 'del_route'

        AnsibleExtraVars = json.dumps(host_params)
        cmdAnsible = ['ansible-playbook','-i',fileInventory,
                '--limit=' + str(hostname),'--tags', ansibleTags,
                '--extra-vars', AnsibleExtraVars, setupPlaybook]
        resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

        # add ip route on IPCS
        message = ''.join([ 'during run command: ', ' '.join(cmdAnsible),
                            '\nRetrun Code: ', str(resAnsible.returncode),
                            '\nstdout: ', resAnsible.stdout,
                            '\nstderr: ', resAnsible.stderr ])

        # print( 'resAnsible.stderr:', resAnsible.stderr )
        # print('exists in inresAnsible.stderr:', 'exists' in resAnsible.stderr)
        if resAnsible.returncode == 0 or 'exists' in resAnsible.stderr:
            return {'status':'ok','message':message}
        else:
            return {'status':'error', 'message':message}

    def isAllReturnStatusOk( resultList ):
        return all([ result.get('status') == 'ok' for result in resultList]) 

    routed.keepClean()

    interface = VPS_dict[hostname].get('interface')
    route = destIP+' dev '+interface
    # print('route:', route, 'interface:', interface)

    cmdResults = []
    # cmdResults.append( setVpsRoute(hostname,srcIP,action) )

    if action == 'add':
        actResult = routed.add2Ctable(srcIP,route)
    else:
        actResult = routed.del2Ctable(srcIP,route)

    cmdResults.append( actResult )
    message = '\n'.join([ result.get('message') for result in cmdResults ])

    if isAllReturnStatusOk( cmdResults ):
        return jsonify({'status':'ok', 'message': message})
    else:
        return jsonify({'status':'error', 'message': message})

def check_vps( hostname, fileInventory=fileInventory, VPS_dict=VPS_dict ):
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

    def delEmptyParams(parameters):
        P = parameters.copy()
        for p in P:
            if P[p] == '':
                parameters.pop(p)

    delEmptyParams(parameters)
    testVpsDict = {hostname:parameters}
    test_inventory=work_dir+'/test.yml'
    write_inventory(test_inventory, testVpsDict)

    check_vps(hostname, test_inventory, testVpsDict)

    if testVpsDict[hostname].get('state') == 'unreachable':
        return jsonify({"status":"error",
            "message":"host seems unreachable for ansible"}), 400

    # id = getAvailableId()
    VPS_dict[hostname] = testVpsDict[hostname].copy()

    host_params = VPS_dict.get(hostname)
    host_params['host_id'] = getAvailableId()
    host_params['interface'] ='tun'+str(host_params.get('host_id'))
    host_params['hostname'] = hostname
    host_params['ip_info'] = getIpLocation(parameters['ansible_host'])
    host_params['configured'] = 'no'
    host_params['routes'] = []

    config_vps(hostname)
    write_inventory(VPS_dict=VPS_dict)
    return jsonify({"status":"ok", "message":"new host added"}), 200


def del_vps( hostname ):
    global VPS_dict
    if hostname not in VPS_dict:
        return jsonify({"status":"error",
                        "message":"'" + str(hostname) + "' no such host"}), 500

    def setRoute( hostname, source, action ):

        # get copy of VPS variables
        host_params = VPS_dict.get(hostname).copy()
        host_params['routes'] = [ {'source':source} ]

        if action == 'add':
            ansibleTags = 'add_route'
        else:
            ansibleTags = 'del_route'

        AnsibleExtraVars = json.dumps(host_params)
        cmdAnsible = ['ansible-playbook','-i',fileInventory,
                '--limit=' + str(hostname),'--tags', ansibleTags,
                '--extra-vars', AnsibleExtraVars, deletePlaybook]
        resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

        # add ip route on IPCS
        message = ''.join([ 'during run command: ', ' '.join(cmdAnsible),
                            '\nRetrun Code: ', str(resAnsible.returncode),
                            '\nstdout: ', resAnsible.stdout,
                            '\nstderr: ', resAnsible.stderr ])

        # print( 'resAnsible.stderr:', resAnsible.stderr )
        # print('exists in inresAnsible.stderr:', 'exists' in resAnsible.stderr)
        if resAnsible.returncode == 0 or 'exists' in resAnsible.stderr:
            return {'status':'ok','message':message}
        else:
            return {'status':'error', 'message':message}

    VPS_dict.pop(hostname)
    write_inventory(VPS_dict=VPS_dict)
    return jsonify({'status':'ok', 'message':'VPS is removed'}), 200
    # TODO add andible secure VPS wiping
    # TODO delete openvpn-client configuration!!!!

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
            VPS_dict[hostname]['configured'] = 'no'
            write_inventory(VPS_dict=VPS_dict)
            return { 'status':'error', 
                'message': 'ansible-playbook return code: ' +
                str(resAnsible.returncode) }
        else:
            VPS_dict[hostname]['configured'] = 'yes'
            write_inventory(VPS_dict=VPS_dict)
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
        confTread = Thread(target=conf_one_vps, args=(hostname,))

    confTread.start()

def formRouteList():
    # TODO rename vars!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    routed.keepClean()
    Ctable = routed.Ctable
    print('Ctable',Ctable)
    inf2hn = { VPS_dict[hn].get('interface'):VPS_dict[hn] for hn in VPS_dict }

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
