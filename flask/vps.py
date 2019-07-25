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

def write_inventory(fileInv=fileInventory):
    global VPS_dict

    inventory = {}
    inventory.setdefault('all', {'children':{'vps':{'hosts':{}}}})

    # TODO rid of unnecessary data in VPS_dict
    #   'hostname'?

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


def route( action, srcIP, hostname, destIP ='0.0.0.0/0', description='' ):

    global VPS_dict 

    if type(srcIP) is not str or srcIP == '':
        return jsonify({ 'status':'error',
            'message': "requested source IP address is not string" }), 500
    if type(hostname) is not str:
        return jsonify({ 'status':'error',
            'message': "requested 'hostname' is not string" }), 500
    if type(destIP) is not str or destIP == '':
        destIP = '0.0.0.0/0'

    try: ipaddress.ip_network(srcIP)
    except ValueError:
        return jsonify({ 'status':'error',
            'message': "'"+ srcIP + "' is bad source IP" }), 400

    try: ipaddress.ip_network(destIP)
    except ValueError:
        return jsonify({ 'status':'error',
            'message': "'"+ destIP + "' is bad destination IP or subnet" }), 400

    if hostname not in VPS_dict:
        return jsonify({ 'status':'error',
            'message': "'" + hostname + "' is bad hostname" }), 400
 
    # check if action is valid
    if action not in ('add', 'delete'):
        return jsonify({ 'status':'error',
            'message': "'"+ str(action) + "' is bad action" }), 200

    ###---vvv--- Functions ---vvv---###

    def isRouteExists( srcIP, destIP, hostname ):
        global VPS_dict
        routes = VPS_dict[ hostname ].get('routes')

        for route in routes:
            if srcIP == route.get('source') and destIP == route.get('destination'):
                return True

        return False

    def formRoute( srcIP, destIP, hostname, description=''):
        global VPS_dict
        routes = VPS_dict[ hostname ].get('routes')

        for route in routes:
            if srcIP == route.get('source') and destIP == route.get('destination'):
                return route
        route = { 'source': srcIP, 
                  'destination': destIP, 
                  'description': description }
        return route

    # IP RULE on IPCS
    def setIpRule( srcIP, destIP , action):
        # check if rule already exists
        ipRuleList = subprocess.run(['ip','rule','list','table','1'], 
                                    capture_output=True, text=True).stdout

        # not quiet shure, maybe better to use regexp:
        if 'from '+ srcIP +' to '+ destIP in ipRuleList:
            return {'status':'ok','message':"rule already done"}

        # add ip rule on IPCS
        cmdIpRuleAdd = ['sudo','ip','rule',action,'from',srcIP,'to',destIP, 'table','1']
        resIpRuleAdd = subprocess.run(cmdIpRuleAdd, capture_output=True, text=True)

        message = ' '.join(['during command: ', ' '.join(cmdIpRuleAdd),
                            '\nRetrun Code: ', str(resIpRuleAdd.returncode),
                            '\nstdout: ', resIpRuleAdd.stdout,
                            '\nstderr: ', resIpRuleAdd.stderr ])

        if resIpRuleAdd.returncode != 0:
            return {'status':'error', 'message':message}
        else:
            return {'status':'ok','message':message}
    
    # IP ROUTE on IPCS
    def setIpRoute( destIP, interface, action ):
        # check if route already exists
        ipRouteList = subprocess.run(['ip','route','list','table','1'], 
                                    capture_output=True, text=True).stdout

        # interface = VPS_dict[hostname]['interface']

        # not quiet shure, maybe better to use regexp
        if destIP +' dev '+ interface in ipRouteList:
            return {'status':'ok','message':"route already done"}

        # add ip route on IPCS
        cmdIpRouteAdd = ['sudo','ip','route',action,destIP,'dev', interface, 'table','1']
        resIpRouteAdd = subprocess.run(cmdIpRouteAdd, capture_output=True, text=True)
        rc = resIpRouteAdd.returncode
        so = resIpRouteAdd.stdout
        se = resIpRouteAdd.stderr
        message = ''.join([ 'During run command: ', ' '.join(cmdIpRouteAdd),
                            '\nRetrun Code: ', str(rc),
                            '\nstdout: ', so,
                            '\nstderr: ', se ])
        if rc == 0:
            return {'status':'ok','message':message}
        elif action == 'add' and 'exists' in se: 
            return {'status':'ok','message':message}
        elif action == 'delete' and "No such process" in se:
            return {'status':'ok','message':message}
        else:
            return {'status':'error', 'message':message}


    # IP ROUTE on VPS
    def setVpsRoute( hostname, route, action ):

        # get copy of VPS variables
        host_params = VPS_dict.get(hostname).copy()
        host_params['routes'] = [ route ]

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

    def isAllOk( steps ):
        return all([ step.get('status') == 'ok' for step in steps ])

    ###---^^^--- Functions ---^^^---###

    # check if route exists for 'add' action
    # and not exists for 'delete' action
    if action == 'add':
        if isRouteExists( srcIP, destIP, hostname):
            return jsonify({ 'status':'ok',
                'message': "route already exists" }), 200
    elif action == 'delete':
        if not isRouteExists( srcIP, destIP, hostname):
            return jsonify({ 'status':'ok',
                'message': "route already not exists" }), 200

    interface = VPS_dict[hostname].get('interface')
    route = formRoute(srcIP, destIP, hostname, description)

    steps = [ 
            setIpRule( srcIP, destIP, action ),
            setIpRoute( destIP, interface, action ),
            setVpsRoute( hostname, route, action )
              ]

    # collect all messages to one message
    # is all statuses is 'ok'?
    msgList = []
    isStatusOkList = []
    for step in steps:
            msgList.append(step.get('message'))
            isStatusOkList.append(step.get('status') == 'ok')
    message = '\n'.join(msgList)
    isAllOk = all(isStatusOkList)
    print(isStatusOkList)
        
    # if 'message' is empty
    if isAllOk:
        if action == 'add':
            VPS_dict[hostname]['routes'].append(route)
        else:
            VPS_dict[hostname]['routes'].remove(route)
        write_inventory()
        return jsonify({'status':'ok', 'message': message }), 200
    else:
        return jsonify({'status':'error', 'message': message }), 500

def check_vps( hostname, fileInventory=fileInventory ):
    # check for availability to work with ansible
    global VPS_dict
    cmdAnsible = ['ansible', hostname,'-i',fileInventory, '-m',
    'ping', '-o']
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

    id = getAvailableId()
    VPS_dict[hostname] = parameters
    host_params = VPS_dict.get(hostname)
    host_params['host_id'] = id
    host_params['interface'] ='tun'+str(host_params.get('host_id'))
    host_params['hostname'] = hostname
    host_params['ip_info'] = getIpLocation(parameters['ansible_host'])
    host_params['configured'] = 'no'
    host_params['routes'] = []

    test_inventory=work_dir+'/test.yml'
    write_inventory(test_inventory)
    check_vps(hostname, test_inventory)
    if VPS_dict[hostname].get('state') == 'available':
        config_vps(hostname)
        write_inventory()
        return jsonify({"status":"ok","message":"new host added"}), 200
    else:
        VPS_dict.pop(hostname)
        return jsonify({"status":"error",
            "message":"host seems unreachable for ansible"}), 400

def del_vps( hostname ):
    global VPS_dict
    if hostname not in VPS_dict:
        return jsonify({"status":"error",
                        "message":"'" + hostname + "' no such host"}), 500

    VPS_dict.pop(hostname)
    write_inventory()
    return jsonify({'status':'ok', 'message':'VPS is removed'}), 200

    # cmdAnsible = ['ansible-playbook','-i',fileInventory,'--limit=' + str(hostname),
    #             deletePlaybook]
    # resAnsible = subprocess.run(cmdAnsible, capture_output=True, text=True)

    # if resAnsible.returncode != 0 :
    #     print('Error during run command:', ' '.join(cmdAnsible),
    #                 '\nRetrun Code: ', resAnsible.returncode,
    #                 '\nstdout: ', resAnsible.stdout,
    #                 '\nstderr: ', resAnsible.stderr)
    #     return jsonify({ 'status':'error', 
    #         'message': 'ansible-playbook return code: ' + str(resAnsible.returncode) }), 500
    # else:
    #     VPS_dict.pop(hostname)
    #     write_inventory()
    #     return jsonify({'status':'ok', 'message':'VPS is removed'}), 200

# def edit_vps( hostname, parameters ):
#     global VPS_dict
#     # check if hostname is exists
#     if hostname not in VPS_dict:
#         return jsonify({"status":"error",
#             "message":"host \'"+hostname+"\' don't exists"}), 400

#     for parameter in parameters:
#         VPS_dict[hostname][parameter] = parameters.get(parameter)
#     write_inventory()
#     check_vps(hostname)

#     return jsonify({"status":"ok","message":"new host added"}), 200

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
            write_inventory()
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
