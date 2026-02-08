#! /usr/bin/env python3
import ipaddress
import urllib.request
from urllib.error import HTTPError
import re
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, 'conf', 'nginx-ipfilter-jp.conf')
DEFAULT_HEADERS = {
    'User-Agent': 'NGINX-IPFILTER-JP-Client/0.1 (https://github.com/kacchan822/nginx-ipfilter)'
}


def get_apnic_data():
    """
        APNIC Extended Allocation and Assignment Reports (Version 2.3) 
        ref: https://www.apnic.net/about-apnic/corporate-documents/documents/resource-guidelines/rir-statistics-exchange-format/
    """
    url = 'http://ftp.apnic.net/stats/apnic/delegated-apnic-extended-latest'
    
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req) as res:
            data = res.read().decode()
    except HTTPError as error:
        print(f'Cant get data: {error}')
        sys.exit(1)

    record_re = re.compile(
        r'^(?P<registry>[a-zA-Z]+)\|JP\|(?P<type>ipv4|ipv6)\|'
        r'(?P<start>[0-9a-f.:]+)\|(?P<value>[0-9]+)\|(?P<date>[0-9]+)\|'
        r'(?P<status>[a-zA-Z]+)\|?(?P<extensions>\S+)?$',
        re.MULTILINE
    )

    iplist = []
    for record in record_re.findall(data):
        if record[1] == 'ipv4':
            ipstart = ipaddress.IPv4Address(record[2])
        else:
            ipstart = ipaddress.IPv6Address(record[2])
        address_counts = int(record[3])
        iplast = ipstart + (address_counts - 1)

        for ipaddr in ipaddress.summarize_address_range(ipstart, iplast):
            if address_counts == ipaddr.num_addresses:
                iplist.append(f'{ipaddr.with_prefixlen} 1;\n')
    
    return iplist


def get_apple_data():
    """
        ref: https://developer.apple.com/jp/support/prepare-your-network-for-icloud-private-relay/
    """
    url = 'https://mask-api.icloud.com/egress-ip-ranges.csv'
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req) as res:
            data = res.read().decode()
    except HTTPError as error:
        print(f'Cant get data: {error}')
        sys.exit(1)

    record_v4_re = re.compile(
        r'^(?P<cidr>[0-9.]+/[0-9]+),JP,(?P<local>\S+),(?P<region>\S+),$',
        re.MULTILINE
    )

    record_v6_re = re.compile(
        r'^(?P<cidr>[0-9a-f:]+/[0-9]+),JP,(?P<local>\S+),(?P<region>\S+),$',
        re.MULTILINE
    )

    iplist = []
    for record in record_v4_re.findall(data):
        iplist.append(f'{record[0]} 1;\n')

    for record in record_v6_re.findall(data):
        iplist.append(f'{record[0]} 1;\n')

    return iplist


with open(OUTPUT_FILE, 'w') as f:
    f.write(f'# created at {datetime.now(timezone.utc).isoformat()}.\n')
    f.write('# from APNIC registered addresses\n')
    f.writelines(get_apnic_data())
    f.write('# from Apple private relay egress ip ranges\n')
    f.writelines(get_apple_data())
    f.write(f'# EOF\n')
