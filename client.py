#!/usr/bin/env python3

import requests
import yaml
import argparse
import os
import shutil

config = os.path.join(os.path.dirname(os.path.realpath(__file__)),"config.yml")

with open(config, "r") as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

term_cols = getattr(shutil.get_terminal_size((80, 20)), 'columns')

def call_api(params, path):
    url = '/'.join((params['base_url'],params['api_path'],path))
    try:
        response = requests.get(url, auth=(params['username'],
                                params['password']))
    except:
        return

    if response.status_code is not 200:
        return

    return response.json()

def print_data(term_cols, key, value, suffix = None):
    if suffix is not None:
        value_cols = term_cols - 26 - len(value)
        print("(0x(B %-18s (0x(B %s %-*.*s (0x(B" %
            (key, value, value_cols, value_cols, suffix))
    else:
        value_cols = term_cols - 25
        print("(0x(B %-18s (0x(B %-*.*s (0x(B" %
            (key, value_cols, value_cols, value))

def sizeof_fmt(num, suffix='B', binary=True):
    if binary:
        units = ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']
        base = 1024.0
    else:
        units = ['','K','M','G','T','P','E','Z']
        base = 1000.0
    for unit in units:
        if abs(num) < base:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= base
    return "%.1f %s%s" % (num, 'Y', suffix)

# Test instances
for instance in list(cfg['instances']):
    test = call_api(cfg['instances'][instance], 'devices')
    if test is None:
        if cfg['debug']: print("Instance %s is not working, disabling" % instance)
        cfg['instances'].pop(instance)
    else:
        if cfg['debug']: print("Instance %s is working" % instance)

def search_ports(args):
    for instance, params in cfg['instances'].items():
        data = call_api(params, 'ports/?ifAlias=%s' % args.string)
        data_devices = call_api(params, 'devices/')
        devices = data_devices['devices']

        if data['count'] < 1:
            print("No port found for description %s on instance %s" %
                (args.string, instance))
            return

        if args.short:
            term_cols = getattr(shutil.get_terminal_size((80, 20)), 'columns')
            value_cols = term_cols - 59

            print("(0l" + "q" * 27 + "w" + "q" * 18 + "w" + "q" * 7 + "w" + "q" * (term_cols - 57) + "k(B")
            print("(0x(B %-25.25s (0x(B %-16.16s (0x(B %-5.5s (0x(B %-*.*s (0x(B" %
                ("Hostname", "Interface", "State", value_cols, value_cols, "Description"))
            print("(0t" + "q" * 27 + "n" + "q" * 18 + "n" + "q" * 7 + "n" + "q" * (term_cols - 57) + "u(B")

        for port in data['ports'].values():
            if port['disabled'] == "1": continue
            if port['deleted'] == "1": continue
            device = devices[port['device_id']]
            if device['disabled'] == "1": continue

            if args.short:
                short_hostname = device['hostname'].split(".",1)[0]
                print("(0x(B %-25.25s (0x(B %-16.16s (0x(B %-5.5s (0x(B %-*.*s (0x(B" %
                    (short_hostname, port['port_label_short'], port['ifOperStatus'], value_cols,
                     value_cols, port['ifAlias']))
                     #value_cols, port['port_descr_descr'] or port['ifAlias']))

            else:
                address = call_api(params, 'address/?device_id=%s&interface=%s' % (port['device_id'], port['port_label_short']))
                address6 = call_api(params, 'address/?af=ipv6&device_id=%s&interface=%s' % (port['device_id'], port['port_label_short']))

                term_cols = getattr(shutil.get_terminal_size((80, 20)), 'columns')

                print("(0l" + "q" * 20 + "w" + "q" * (term_cols - 23) + "k(B")

                print_data(term_cols, "Device", device['hostname'])
                print_data(term_cols, "", "%s/device/device=%s" %
                    (params['base_url'], port['device_id']))
                print_data(term_cols, "Hardware", device['hardware'])
                print_data(term_cols, "Port", port['port_label_short'])
                print_data(term_cols, "", "%s/device/device=%s/tab=port/port=%s/" %
                    (params['base_url'], port['device_id'], port['port_id']))
                print_data(term_cols, "Description", port['ifAlias'])
                print_data(term_cols, "Port status", "%s (Admin) / %s (Oper)" %
                    (port['ifAdminStatus'], port['ifOperStatus']))
                print_data(term_cols, "Last change", port['ifLastChange'])
                print_data(term_cols, "Speed", port['ifHighSpeed'], "Mbps")
                print_data(term_cols, "Duplex", port['ifDuplex'])
                print_data(term_cols, "MTU", port['ifMtu'])
                for ip in address['addresses']:
                    print_data(term_cols, "IP address", "%s/%s" % (ip['ipv4_address'],ip['ipv4_prefixlen']))

                for ip6 in address6['addresses']:
                    print_data(term_cols, "IPv6 address", "%s/%s" % (ip6['ipv6_compressed'],ip6['ipv6_prefixlen']))
                print_data(term_cols, "Input rate", "%s (%s)" % (
                    sizeof_fmt(int(port['ifInOctets_rate']),suffix='Bps'),
                    sizeof_fmt(int(port['ifInOctets_rate'])*8,suffix='bps',binary=False),
                    )
                )
                print_data(term_cols, "Output rate", "%s (%s)" % (
                    sizeof_fmt(int(port['ifOutOctets_rate']),suffix='Bps'),
                    sizeof_fmt(int(port['ifOutOctets_rate'])*8,suffix='bps',binary=False),
                    )
                )
                print_data(term_cols, "Input errors rate", port['ifInErrors_rate'])
                print_data(term_cols, "Output errors rate", port['ifOutErrors_rate'])

                print("(0m" + "q" * 20 + "v" + "q" * (term_cols - 23) + "j(B")

        if args.short:
            print("(0m" + "q" * 27 + "v" + "q" * 18 + "v" + "q" * 7 + "v" + "q" * (term_cols - 57) + "j(B")

def search_devices(args):
    if args.field == "location":
        args.field = "location_text"

    for instance, params in cfg['instances'].items():
        data = call_api(params, 'devices/?%s=%s' % (args.field, args.string))

        if data['count'] < 1:
            print("No device found for description %s on instance %s" %
                (args.string, instance))
            return

        if args.short:
            term_cols = getattr(shutil.get_terminal_size((80, 20)), 'columns')
            value_cols = term_cols - 61

            print("(0l" + "q" * 27 + "w" + "q" * 28 + "w" + "q" * (term_cols - 59) + "k(B")
            print("(0x(B %-25.25s (0x(B %-26.26s (0x(B %-*.*s (0x(B" %
                ("Hostname", "Hardware", value_cols, value_cols, "Serial"))
            print("(0t" + "q" * 27 + "n" + "q" * 28 + "n" + "q" * (term_cols - 59) + "u(B")

        for device in data['devices'].values():
            if device['disabled'] == "1": continue

            if args.short:
                short_hostname = device['hostname'].split(".",1)[0]
                print("(0x(B %-25.25s (0x(B %-26.26s (0x(B %-*.*s (0x(B" %
                (short_hostname,
                 " ".join([device['vendor'] or "", device['hardware'] or ""]),
                 value_cols, value_cols, device['serial']))
            else:
                term_cols = getattr(shutil.get_terminal_size((80, 20)), 'columns')
                print("(0l" + "q" * 20 + "w" + "q" * (term_cols - 23) + "k(B")
                print_data(term_cols, "Device", device['hostname'])
                print_data(term_cols, "", "%s/device/device=%s" %
                    (params['base_url'], device['device_id']))
                print_data(term_cols, "System name", device['sysName'])
                print_data(term_cols, "Hardware", " ".join([device['vendor'] or "", device['hardware'] or ""]))
                print_data(term_cols, "Software version",
                  " ".join([device['os_text'],
                            device['version'] or ""]))
                if device['features']:
                    print_data(term_cols, "Features", device['features'])
                print_data(term_cols, "Serial number", device['serial'])
                print_data(term_cols, "Location", device['location'])
                print("(0m" + "q" * 20 + "v" + "q" * (term_cols - 23) + "j(B")

        if args.short:
            print("(0m" + "q" * 27 + "v" + "q" * 28 + "v" + "q" * (term_cols - 59) + "j(B")


# Argument parsing
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='Action to perform',dest='action')

parser_search_port_by_descr = subparsers.add_parser('search_ports', help="Search ports by description")
parser_search_port_by_descr.add_argument('string', type=str, help="String to search")
parser_search_port_by_descr.add_argument('-s', '--short', action='store_true')

parser_search_device = subparsers.add_parser('search_devices', help="Search devices")
parser_search_device.add_argument('field', choices=['hostname', 'location', 'hardware', 'serial'], help="Field to use for search")
parser_search_device.add_argument('string', type=str, help="String to search")
parser_search_device.add_argument('-s', '--short', action='store_true')

args = parser.parse_args()
globals()[args.action](args)
