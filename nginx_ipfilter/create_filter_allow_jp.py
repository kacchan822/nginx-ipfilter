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

url = 'http://www.apnic.net/stats/apnic/delegated-apnic-extended-latest'
headers = {'User-Agent': 'NGINX-IPFILTER-JP-Client/0.1 (https://github.com/kacchan822/nginx-ipfilter)'}
req = urllib.request.Request(url, headers=headers)
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

with open(OUTPUT_FILE, 'w') as f:
    f.write(f'# created at {datetime.now(timezone.utc).isoformat()}.\n')
    f.writelines(iplist)
