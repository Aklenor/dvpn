#!/usr/bin/env python

from backend import app
from flask import request
from flask import jsonify
import os
import sys
import vps

ansible_playbook = 'roles/setup.yml'
vps.get_vps_list()

@app.route('/')
def health():
    return jsonify({"status":"ok","message":"I'm alive"}),200

@app.route('/availablevps')
def getVpsList():
    return jsonify(vps.servers_list), 200

@app.route('/add_vps', methods=["POST"])
def add_vps():
    hostname = request.form.get('hostname')
    params = request.form.get('params')
    return vps.add_vps( hostname, params )

@app.route('/add_route', methods=["POST"])
def add_route():
    src = request.remote_addr
    dst = request.form.get('destination')
    hostname = request.form.get('hostname')
    return vps.add_route( src, dst, hostname )

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
