#!/usr/bin/env python

import requests
import yaml
import argparse

with open("config.yml", "r") as ymlfile:
    cfg = yaml.load(ymlfile)

def call_api(path):
    url = '/'.join((cfg['base_url'],cfg['api_path'],path))
    response = requests.get(url, auth=(cfg['username'], cfg['password']))
    return response.json()

def print_data(key, value, suffix = None):
    if suffix is not None:
        print "%-20s %s %s" % (key, value, suffix)
    else:
        print "%-20s %s" % (key, value)

def search_ports(args):
    data = call_api('ports/?ifAlias=%s' % args.string)

    if data['count'] < 1:
        print "No port found matching description %s" % args.string
        return

    for port in data['ports'].itervalues():
        print "=" * 80
        device = call_api('devices/%s' % port['device_id'])
        print_data("Device", device['device']['hostname'])
        print_data("", "%s/device/device=%s" % (cfg['base_url'], port['device_id']))
        print_data("Port", port['port_label_short'])
        print_data("", "%s/device/device=%s/tab=port/port=%s/" %
            (cfg['base_url'], port['device_id'], port['port_id']))
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
