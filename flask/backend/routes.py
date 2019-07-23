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
vps.conf_all_vps()

@app.route('/')
def health():
    return jsonify({"status":"ok","message":"I'm alive"})

@app.route('/availablevps', methods=['GET'])
def getVpsList():
    return jsonify(vps.VPS_dict)

@app.route('/add_vps', methods=["POST"])
def add_vps():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()
    hostname = content.get('hostname')
    params = content.get('parameters')
    return vps.add_vps( hostname, params )

@app.route('/del_vps', methods=["POST"])
def del_vps():
    hostname = request.form.get('hostname')
    return vps.del_vps( hostname )

@app.route('/edit_vps', methods=["POST"])
def edit_vps():
    content = request.get_json()
    hostname = content.get('hostname')
    parameters = content.get('parameters')
    return vps.edit_vps( hostname , parameters )

@app.route('/add_route', methods=["POST"])
def add_route():
    src = request.remote_addr
    dst = request.form.get('destination')
    hostname = request.form.get('hostname')
    descr = request.form.get('description')
    return vps.add_route(src, dst, hostname, descr)

# @app.route('/del_route', methods=["POST"])
# def del_route():
#     src = request.remote_addr
#     dst = request.form.get('destination')
#     hostname = request.form.get('hostname')
#     descr = request.form.get('description')
#     return vps.del_route(src, dst, hostname, descr)

@app.route('/config_vps', methods=["POST"])
def config_vps():
    hostname = request.form.get('hostname')
    vps.config_in_thread(hostname)
    return jsonify({"status":"test","message":"configuring vps"})
