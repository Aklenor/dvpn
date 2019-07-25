#!/usr/bin/env python

from backend import app
from flask import request
from flask import jsonify
import os
import sys
import vps
import pdb

ansible_playbook = 'roles/setup.yml'
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

# @app.route('/edit_vps', methods=["POST"])
# def edit_vps():
#     content = request.get_json()
#     hostname = content.get('hostname')
#     parameters = content.get('parameters')
#     return vps.edit_vps( hostname , parameters )

@app.route('/add_route', methods=["POST"])
def add_route():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()

    src = content.get('source')
    if src is None or src == '':
        src = request.remote_addr

    dst = content.get('destination')
    hostname = content.get('hostname')
    descr = content.get('description')

    return vps.route('add', src, hostname, dst, descr )

@app.route('/del_route', methods=["POST"])
def del_route():
    if not request.is_json:
        return jsonify({"status":"error","message":"request in not json"}), 400
    content = request.get_json()

    src = content.get('source')
    if src is None:
        src = request.remote_addr

    dst = content.get('destination')
    hostname = content.get('hostname')
    descr = content.get('description')

    return vps.route('delete', src, hostname, dst, descr )

# @app.route('/del_route', methods=["POST"])
# def del_route():
#     src = request.remote_addr
#     dst = request.form.get('destination')
#     hostname = request.form.get('hostname')
#     descr = request.form.get('description')
#     return vps.del_route(src, dst, hostname, descr)

# @app.route('/config_vps', methods=["POST"])
# def config_vps():
#     hostname = request.form.get('hostname')
#     vps.config_vps(hostname)
#     return jsonify({"status":"test","message":"configuring vps"})
