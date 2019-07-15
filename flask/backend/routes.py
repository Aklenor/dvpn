#!/usr/bin/env python

from backend import app
from flask import request
from flask import jsonify
import os
import sys
import subprocess
import vps

ansible_playbook = 'roles/setup.yml'
vps.get_vps_list()

@app.route('/')
def health():
    return {"status":"ok","message":"I'm alive"}

@app.route('/availablevps')
def getVpsList():
    return vps.servers_list, 200

@app.route('/add_route', methods=["POST"])
def add_route():
    dst = request.form.get('destination')
    host = request.form.get('vps')

    return vps.add_route( dst, host )

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
