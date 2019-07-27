#!/usr/bin/python
import subprocess

# client table
Ctable={
        '10.1.1.244':{
            'tid':1,
            'rule':"from 10.1.1.244 lookup 1",
            'routes':{
                'default': "default dev tun0 scope link",
                '1.1.1.1': "1.1.1.1 dev tun1 scope link"
                }
            },
        '10.1.1.243':{
            'tid':2,
            'rule':"from 10.1.1.243 lookup 2",
            'routes':{
                'default': "default dev tun2 scope link",
                '8.8.8.8': "8.8.8.8 dev tun1 scope link"
                }
            }
        }

# TODO iproute2 can output json!!!!

def getSysRules(tid=None):
    if tid is None:
        table = ''
    else:
        table = 'table '+str(tid)

    cmd = 'ip rule list ' + table
    cmd = cmd.split()
    sysRuleList = subprocess.run(cmd, capture_output=True, text=True).stdout.split('\n')
    sysRuleList.remove('')

    # remove system rules from list:
    default_rules = ['0:\tfrom all lookup local',
                     '32766:\tfrom all lookup main',
                     '32767:\tfrom all lookup default']

    PRIORITY_PART = 0
    RULE_PART= 1

    ruleList = [rule.split('\t')[RULE_PART] for rule in sysRuleList if rule not in default_rules]
    return ruleList

def getSysRoutes(tid):
    cmd = 'ip route show table '+str(tid)
    command = cmd.split()
    RouteList = subprocess.run(command, capture_output=True, text=True).stdout.split('\n')
    RouteList.remove('')

    DESTINATION_PART = 0
    RouteDict = { route.split()[DESTINATION_PART]:route for route in RouteList }

    return RouteDict

def GetTid():
    global Ctable

    # IDs = Ctable.keys()
    IDs = [ parameters.get('tid') for parameters in Ctable.values()]
    if len(IDs) == 0:
        return 1

    findMinFreeElem = min( set(range(1,max(IDs)+2)) - set(IDs) )
    return findMinFreeElem

def add2Ctable(src, route):
    global Ctable

    DESTINATION_PART = 0
    dst = route.split()[DESTINATION_PART]

    # TODO route validity check

    def createNewClient(src):
        # create new entity in Ctable
        tid = GetTid()
        rule = 'from ' + str(src) + ' lookup ' + str(tid)
        flushRouteTable(tid)

        Ctable[src] = {'tid':tid,
                       'rule':rule,
                       'routes': {}}

        print("new client added to rules:", Ctable[src])

    if src not in Ctable:
        createNewClient(src)

    client = Ctable.get(src)
    tid = client.get('tid')

    delMessage = ""
    if dst in client.get('routes'):
        print('remove old route')
        delResult = del2Ctable(src, dst)
        delResult['message'] = "Delete Old Route:\n"+delResult.get('message')
        delMessage = delResult.get('message')

        if delResult.get('status') == 'error':
            return delResult

    addResult =addRoute(route,tid)
    message = delMessage + formMessage(addResult)

    if addResult.get('rc') != 0:
        print("add2Ctable error:",message)
        return {'status':'error','message':message}
    else:
        client['routes'][dst] = route
        print("add2Ctable ok:",message)
        return {'status':'ok','message':message}

def del2Ctable(src, route):
    global Ctable

    DESTINATION_PART = 0
    dst = route.split()[DESTINATION_PART]

    if src not in Ctable:
        message = "rule for", src, "not exists"
        print("del2Ctable error:", message)
        return {'status':'error','message':message}

    routes = Ctable[src].get('routes')
    if dst not in routes:
        message = "route '"+dst+" not exists"
        print("del2Ctable error:",message)
        return {'status':'error','message':message}

    tid = Ctable[src].get('tid')

    cmdResult = delRoute(route,tid)
    message = formMessage(cmdResult)

    if cmdResult.get('rc') != 0:
        print("del2Ctable error:", message)
        return {'status':'error', 'message': message}
    else:
        routes.pop(dst)
        print("del2Ctable ok:", message)
        return {'status':'ok', 'message':message}

def exeCmd(cmd):
    cmdResult = subprocess.run(cmd, capture_output=True, text=True)

    cmd = ' '.join(cmd)
    rc = cmdResult.returncode
    stdout = cmdResult.stdout
    stderr = cmdResult.stderr

    print('cmd:', cmd,
          '\nrc:',rc,
          '\nstdout:',stdout,
          '\nstderr:',stderr)
    return {'cmd':cmd, 'rc':rc, 'stdout':stdout, 'stderr':stderr}

def formMessage(cmdResult):
    print('fromMessage:', cmdResult)
    message = ''.join([ 'during run command: ', cmdResult.get('cmd'),
                        '\nRetrun Code: ', str(cmdResult.get('rc')),
                        '\nstdout: ', str(cmdResult.get('stdout')),
                        '\nstderr: ', str(cmdResult.get('stderr'))])
    return message

def addRule(rule):
    cmd = 'sudo ip rule add ' + rule
    cmd = cmd.split()
    return exeCmd(cmd)

def delRule(rule):
    cmd = 'sudo ip rule delete ' + rule
    cmd = cmd.split()
    return exeCmd(cmd)

def addRoute(route, tid):
    cmd = 'sudo ip route add ' + route +' table ' + str(tid)
    cmd = cmd.split()
    return exeCmd(cmd)

def delRoute(route, tid):
    cmd = 'sudo ip route delete ' + route +' table ' + str(tid)
    cmd = cmd.split()
    return exeCmd(cmd)

def flushRouteTable(tid):
    cmd = 'sudo ip route flush table '+str(tid)
    cmd = cmd.split()
    return exeCmd(cmd)

def keepClean():

    for src, params in Ctable.items():
        tid = params.get('tid')

        appRoutes = set(Ctable[src]['routes'].values())
        sysRoutes = set(getSysRoutes(tid).values())

        routes2del = sysRoutes - appRoutes
        routes2add = appRoutes - sysRoutes

        for route in routes2del:
            delRoute(route, tid)
        for route in routes2add:
            addRoute(route, tid)

    #clean rules without routes
    clients2del = []
    for src,client in Ctable.items():
        if len(client.get('routes')) == 0:
            clients2del.append(src)

    for client in clients2del:
        Ctable.pop(client)

    sysRules = set(getSysRules())
    appRules = { value.get('rule') for value in Ctable.values()}

    rules2del = sysRules - appRules
    rules2add = appRules - sysRules

    for rule in rules2del:
        delRule(rule)
    for rule in rules2add:
        addRule(rule)


