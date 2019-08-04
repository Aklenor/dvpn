#!/usr/bin/env python

from backend import app
from flask import request
from flask import jsonify
import os
import sys
import vps
import pdb

HOME_DIR = os.path.expanduser("~")
for *_,files in os.walk(HOME_DIR+'/.ssh/'):
    for file in files:
        if '.pub' in file:
            SSH_KEY_FILE_PATH = HOME_DIR+'/.ssh/'+file

vps.read_inventory()
print('ready to go')

@app.route('/')
def health():
    return jsonify({"status":"ok","message":"I'm alive"})

@app.route('/availablevps', methods=['GET'])
def getVpsList():
    response = jsonify(vps.VPS_dict)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/getroutes', methods=['GET'])
def routes():
    src = request.remote_addr
    RouteList = vps.formRouteList()
    return jsonify({'your_ip':src,'clients':RouteList}), 200

@app.route('/getpubkey', methods=['GET'])
def getPubKey():
    with open(SSH_KEY_FILE_PATH, 'r') as stream:
           pubkey = stream.readlines()

    return jsonify({'pubkey':pubkey}), 200

@app.route('/add_vps', methods=["POST"])
def add_vps():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()
    hostname = content.get('hostname')
    params = content.get('parameters',{})
    return vps.add_vps( hostname, params )

@app.route('/del_vps', methods=["POST"])
def del_vps():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()
    hostname = content.get('hostname')
    return vps.del_vps( hostname )

@app.route('/add_route', methods=["POST"])
def add_route():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()

    src = content.get('source',request.remote_addr)
    if src == '':
        src = request.remote_addr
    dst = content.get('destination')
    if dst == 'default':
        dst = '0.0.0.0/0'
    hostname = content.get('hostname')
    descr = content.get('description','')
    return vps.route('add', src, hostname, dst, descr )

@app.route('/del_route', methods=["POST"])
def del_route():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()

    src = content.get('source', request.remote_addr)
    if src == '':
        src = request.remote_addr
    dst = content.get('destination')
    if dst == 'default':
        dst = '0.0.0.0/0'
    hostname = content.get('hostname')
    descr = content.get('description','')
    return vps.route('delete', src, hostname, dst, descr )
