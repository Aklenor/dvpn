#!/usr/bin/env python

from backend import app
from flask import request
from flask import jsonify
import os
import sys
import vps

ansible_playbook = 'roles/setup.yml'
vps.read_inventory()
vps.fix_inventory()

@app.route('/')
def health():
    return {"status":"ok","message":"I'm alive"}

@app.route('/availablevps', methods=['GET'])
def getVpsList():
    return jsonify(vps.get_vps_list())

@app.route('/add_vps', methods=["POST"])
def add_vps():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()
    hostname = content.get('hostname')
    params = content.get('params')
    return vps.add_vps( hostname, params )

@app.route('/del_vps', methods=["POST"])
def del_vps():
    hostname = request.form.get('hostname')
    # return vps.del_vps( hostname )
    return jsonify({"status":"tmp","message":"hostname '" + hostname + "' is deleted"}), 200

@app.route('/add_route', methods=["POST"])
def add_route():
    src = request.remote_addr
    dst = request.form.get('destination')
    hostname = request.form.get('hostname')
    return jsonify({"status":"tmp","message":"route added from: "+ src+ " to:"+dst+ " via "+ hostname }), 200
    # return vps.add_route( src, dst, hostname )

    # command = subprocess.Popen(['ansible-playbook',ansible_playbook],
    #             cwd='../',
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.STDOUT,
    #             universal_newlines=True,) 
    # stdout,stderr = command.communicate()
    # command1 = subprocess.call("pwd")
    # print(command1)
    # print(stdout)
    # print(stderr)
    # return stdout, stderr
    #check git config
