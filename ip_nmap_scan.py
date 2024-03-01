import subprocess
import re
import json

def scan_network(ip_range):
    command = f'nmap -sn {ip_range}'
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)

    hosts_data = []

    if result.returncode == 0:
        # Extraer las IPs y nombres de host usando expresiones regulares
        pattern = re.compile(r'Nmap scan report for (.+) \((\d+\.\d+\.\d+\.\d+)\)')
        matches = pattern.findall(result.stdout)

        for i, match in enumerate(matches, start=1):
            host_name, ip = match
            key = f'host_{i}'
            hosts_data.append({'Host': host_name, 'IP': ip, 'Status':'Activo'})

    else:
        print(f'Error: {result.stderr}')
    return hosts_data
