#!/usr/bin/env python

import requests
import yaml
import argparse
import os

config = os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.yml")

with open(config, "r") as ymlfile:
    cfg = yaml.load(ymlfile)

def call_api(params, path):
    url = '/'.join((params['base_url'],params['api_path'],path))
    try:
        response = requests.get(url, auth=(params['username'], params['password']))
    except:
        return

    if response.status_code is not 200:
        return

    return response.json()

def print_data(key, value, suffix = None):
    if suffix is not None:
        print "%-20s %s %s" % (key, value, suffix)
    else:
        print "%-20s %s" % (key, value)

# Test instances
for instance in cfg['instances'].keys():
    test = call_api(cfg['instances'][instance], 'devices')
    if test is None:
        print "Instance %s is not working, disabling" % instance
        cfg['instances'].pop(instance)
    else:
        print "Instance %s is working" % instance

def search_ports(args):
    for instance, params in cfg['instances'].iteritems():
        data = call_api(params, 'ports/?ifAlias=%s' % args.string)

        if data['count'] < 1:
            print "No port found for description %s on instance %s" \
                % (args.string, instance)
            return

        for port in data['ports'].itervalues():
            device = call_api(params, 'devices/%s' % port['device_id'])

            if device['device']['disabled'] == "1": continue
            if port['disabled'] == "1": continue

            print "=" * 80
            print_data("Device", device['device']['hostname'])
            print_data("", "%s/device/device=%s" % (params['base_url'], port['device_id']))
            print_data("Port", port['port_label_short'])
            print_data("", "%s/device/device=%s/tab=port/port=%s/" %
                (params['base_url'], port['device_id'], port['port_id']))
            print_data("Description", port['ifAlias'])
            print_data("Port status", "%s (Admin) / %s (Oper)" % (port['ifAdminStatus'], port['ifOperStatus']))
            print_data("Last flap", port['ifLastChange'])
            print_data("Speed", port['ifHighSpeed'], "Mbps")
            print_data("Duplex", port['ifDuplex'])
            print_data("Input rate", port['ifInOctets_rate'], "octets")
            print_data("Output rate", port['ifOutOctets_rate'], "octets")
            print_data("Input errors rate", port['ifInErrors_rate'])
            print_data("Output errors rate", port['ifOutErrors_rate'])

# Argument parsing
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='Action to perform',dest='action')
parser_search_port_by_descr = subparsers.add_parser('search_ports', help="Search ports by description")
parser_search_port_by_descr.add_argument('string', type=str, help="String to search")

args = parser.parse_args()
globals()[args.action](args)
