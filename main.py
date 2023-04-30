import json
import requests
import sys
import csv
import time
import re
import os
from os import environ as env
from dotenv import load_dotenv

requests.packages.urllib3.disable_warnings()
load_dotenv()

NAUTOBOT_HEADERS = {
    "Authorization": f"Token {env['NAUTOBOT_TOKEN']}",
    "Content-Type": "application/json",
}
DEVICE_API = "https://" + env['DEVICE_IP'] + ":" + env['DEVICE_PORT'] + \
    "/restconf/proxy/https://sandbox-iosxe-latest-1.cisco.com:443/restconf/data/"
DEVICE_HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}

VALIDATION_RULES = []
REPORT_FIELDS = ['Device', 'Role', 'Interface', 'Type', 'IP Address (Nautobot)', 'IP Address (Device)', 'Actions']
FORCE_MODE = False

# Nautobot Functions
def get_devices():
    devices_endpoint = f"{env['NAUTOBOT_API']}dcim/devices/"
    response = requests.get(devices_endpoint, headers=NAUTOBOT_HEADERS)
    devices = response.json()["results"]
    return devices

def get_interfaces(device_id):
    interfaces_endpoint = f"{env['NAUTOBOT_API']}dcim/interfaces/?device_id={device_id}"
    response = requests.get(interfaces_endpoint, headers=NAUTOBOT_HEADERS)
    interfaces = response.json()["results"]
    return interfaces

def get_ip_addresses(interface_id):
    ip_addresses_endpoint = f"{env['NAUTOBOT_API']}ipam/ip-addresses/?interface_id={interface_id}"
    response = requests.get(ip_addresses_endpoint, headers=NAUTOBOT_HEADERS)
    ip_addresses = response.json()["results"]
    return ip_addresses

# Device Funcitpns
def getInterfaces():

    url = DEVICE_API + "ietf-interfaces:interfaces"
    response = requests.get(url, headers=DEVICE_HEADERS, auth=(
        env['DEVICE_USERNAME'], env['DEVICE_PASSWORD']), verify=False).json()
    interfaces = response['ietf-interfaces:interfaces']['interface']

    return interfaces

def getInterfaceInformation(interfaceName):

    url = DEVICE_API + "ietf-interfaces:interfaces"
    response = requests.get(url, headers=DEVICE_HEADERS, auth=(
        env['DEVICE_USERNAME'], env['DEVICE_PASSWORD']), verify=False).json()
    interfaces = response['ietf-interfaces:interfaces']['interface']

    for interface in interfaces:
        if interface['name'] == interfaceName:
            try:
                interfaceName = interface['name']
                interfaceDescription = interface['description']
            except:
                interfaceName = 'Interface is not defined!'
                interfaceDescription = ''
            try:
                interfaceIp = interface['ietf-ip:ipv4']['address'][0]['ip']
            except:
                interfaceIp = 'IP address is not defined!'
            return interfaceName, interfaceDescription, interfaceIp

    return False, False, False

def setInterfaceIpAddress(interfaceName, ipAddress, subnetMask, action):

    if "GigabitEthernet" in interfaceName:
        type = "iana-if-type:ethernetCsmacd"
    elif "Loopback" in interfaceName:
        type = "iana-if-type:softwareLoopback"

    payload = {
        "ietf-interfaces:interface": {
            "name": interfaceName,
            "description": "CREATE_L1_RESTCONFF",
            "type": type,
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [
                    {
                        "ip": ipAddress,
                        "netmask": subnetMask
                    }
                ]
            }
        }
    }

    if action == 'edit':
        url = DEVICE_API + 'ietf-interfaces:interfaces/interface=' + interfaceName
        response = requests.put(url, headers=DEVICE_HEADERS, auth=(
            env['DEVICE_USERNAME'], env['DEVICE_PASSWORD']), data=json.dumps(payload), verify=False)
        if response.status_code == 204:
            return True
        else:
            return False
    elif action == 'create':
        url = DEVICE_API + 'ietf-interfaces:interfaces'
        response = requests.post(url, headers=DEVICE_HEADERS, auth=(
            env['DEVICE_USERNAME'], env['DEVICE_PASSWORD']), data=json.dumps(payload), verify=False)
        if response.status_code == 201:
            return True
        else:
            return False
    elif action == 'delete':
        url = DEVICE_API + 'ietf-interfaces:interfaces/interface=' + interfaceName
        response = requests.delete(url, headers=DEVICE_HEADERS, auth=(
            env['DEVICE_USERNAME'], env['DEVICE_PASSWORD']), verify=False)
        if response.status_code == 204:
            return True
        else:
            return False

def checkInterfaceInformation(interfaceName):

    url = DEVICE_API + "ietf-interfaces:interfaces"
    response = requests.get(url, headers=DEVICE_HEADERS, auth=(
        env['DEVICE_USERNAME'], env['DEVICE_PASSWORD']), verify=False).json()
    interfaces = response['ietf-interfaces:interfaces']['interface']

    for interface in interfaces:
        if interface['name'] == interfaceName:
            try:
                interfaceIp = interface['ietf-ip:ipv4']['address']
            except:
                interfaceIp = 'IP address is not defined!'
            return interfaceIp

    return False

# Validation Functions
def validateData(deviceRole, variable, data):
    for rule in VALIDATION_RULES:
        if rule["role"] == deviceRole and rule['text'] == variable:
            status = re.search(rule["regex"], data)
            if status:
                return True
            else:
                return False
    return True

# Report Functions
def prepareReport(rows):

    filename = "Report_" + time.strftime("%d-%m-%Y-%H:%M%:S") + '.csv'

    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(REPORT_FIELDS)
        csvwriter.writerows(rows)

# Other
def init():

    # Check argument
    if len( sys.argv ) > 1:
        if sys.argv[1] == "-f":
            global FORCE_MODE
            FORCE_MODE = True
        else:
            print("Unkown argument! Use '-f' to enable force mode!")
            sys.exit()

    # config.json
    try:
        path = os.path.join(sys.path[0], "rules.json")
        data = open(path, 'r', encoding='utf-8')
        data = json.load(data)
        global VALIDATION_RULES 
        VALIDATION_RULES = data["rules"]
    except:
        print("rules.json is not loaded!")
        sys.exit()

def cidr_to_netmask(cidr):
  cidr = int(cidr)
  mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
  return (str( (0xff000000 & mask) >> 24)   + '.' +
          str( (0x00ff0000 & mask) >> 16)   + '.' +
          str( (0x0000ff00 & mask) >> 8)    + '.' +
          str( (0x000000ff & mask)))

# MAIN
if __name__ == "__main__":
    init()

    # Report
    tempReportFields = []

    # Get devices (nautubot)
    devices = get_devices()
    for device in devices: 
      tempReportField = []
      deviceName = device["name"]
      deviceType = device['device_type']['display']
      deviceRole = device['device_role']['display']

      # Validation according to device role
      if not validateData(deviceRole, "hostname", deviceName):
        print("Device: " + deviceName + "(" + deviceType + "). The device name does not conform to the specified format!")
        tempReportField.append("The device name does not conform to the specified format!")
        break
      else:
        print("Device: " + deviceName + "(" + deviceType + ")")
      print("Role: " + deviceRole)

      # Get device's interfaces (nautubot)
      interfaces = get_interfaces(device["id"])
      for interface in interfaces:
        tempReportField = []
        interface_name = interface["name"]
        type = interface["type"]["value"]
        print("\tInterface: " + interface_name)
        print("\tType: " + type)
        tempReportField.append(deviceName + "(" + deviceRole + ")")
        tempReportField.append(deviceRole)
        tempReportField.append(interface_name)
        tempReportField.append(type)

        # Get device's ip addresses (nautubot)
        ip_addresses = get_ip_addresses(interface["id"])
        for ip_address in ip_addresses:
            ip_address_value = ip_address["address"].split('/')[0]
            ip_address_netmask = ip_address["address"].split('/')[1]
            tempReportField.append(ip_address_value + "/" + ip_address_netmask)

            # Validation according to device role
            if not validateData(deviceRole, "ip_address", ip_address_value):
                print("\tIP address on nautobot: " + ip_address_value + "/" + ip_address_netmask + "(IP address and netmask is not valid, skipped!)")
                tempReportField.append("IP address on nautobot: " + ip_address_value + "/" + ip_address_netmask + "(IP address and netmask is not valid, skipped!)")
            else:
                print("\tIP address on nautobot: " + ip_address_value + "/" + ip_address_netmask + "(IP address and netmask is valid!)")

                # Get device's ip addresses (device)
                interfaceName, interfaceDescription, interfaceIp = getInterfaceInformation(interface_name)

                # Add interface and ip to device
                if not interfaceName or not interfaceDescription:
                    print("\tIP address on device: Interface and IP address is not defined!")
                    tempReportField.append("Interface and IP address is not defined!")

                    # Create interface and ip on device wihtout user approval (force mode)
                    if FORCE_MODE:
                        status = setInterfaceIpAddress(interface_name,ip_address_value, cidr_to_netmask("24"), 'create')
                        if status:
                            print("\tInterface and IP address are added!")
                            tempReportField.append("Interface and IP address are added!")
                        else:
                            print("\tError occured while adding interface and IP address!")
                            tempReportField.append("Error occured while adding interface and IP address!")
                        break
                    # Get user approval
                    else:
                        while True:
                            answer = input("\tDo you confirm to add interface and IP address? (Y/N)")

                            # Edit interface and ip on device
                            if answer.lower() == "y":
                                status = setInterfaceIpAddress(interface_name,ip_address_value, cidr_to_netmask("24"), 'create')
                                if status:
                                    print("\tInterface and IP address are added!")
                                    tempReportField.append("Interface and IP address are added!")
                                else:
                                    print("\tError occured while adding interface and IP address!")
                                    tempReportField.append("Error occured while adding interface and IP address!")
                                break

                            # Skip operation
                            elif answer.lower() == "n":
                                print("\tIP address change was not confirmed, operation was skipped.") 
                                tempReportField.append("IP address change was not confirmed, operation was skipped.")
                                break

                            # Invalid input
                            else:
                                print("\tPlease provide only 'yes' or 'no' as an answer.")

                # Compare nautobot and device information
                else:
                    print("\tIP address on device: " + interfaceIp)
                    tempReportField.append(interfaceIp)

                    if ip_address_value == interfaceIp:
                        print("\tIP addresses are same!")
                        tempReportField.append("IP addresses are same!")

                    else:
                        print("\tIP address diffrence is dedected!")

                        # Edit interface and ip on device wihtout user approval (force mode)
                        if FORCE_MODE:
                            status = setInterfaceIpAddress(interface_name,ip_address_value, cidr_to_netmask("24"), 'edit')
                            if status:
                                print("\tIP address are edited!")
                                tempReportField.append("IP address are edited!")
                            else:
                                print("\tError occured while editng interface and IP address!")
                                tempReportField.append("Error occured while editng interface and IP address!")
                            break
                        # Get user approval
                        else:
                            while True: # --force diye flag ekleyelim scripte. otomatik değişsin
                                answer = input("\tDo you confirm to change IP address? (Y/N)")

                                # Edit interface and ip on device
                                if answer.lower() == "y":
                                    status = setInterfaceIpAddress(interface_name,ip_address_value, cidr_to_netmask("24"), 'edit')
                                    if status:
                                        print("\tIP address are edited!")
                                        tempReportField.append("IP address are edited!")
                                    else:
                                        print("\tError occured while editng interface and IP address!")
                                        tempReportField.append("Error occured while editng interface and IP address!")
                                    break

                                # Skip operation
                                elif answer.lower() == "n":
                                    print("\tIP address change was not confirmed, operation was skipped.") 
                                    tempReportField.append("IP address change was not confirmed, operation was skipped.")
                                    break

                                # Invalid input
                                else:
                                    print("\tPlease provide only 'yes' or 'no' as an answer.")
        print("\n")

        # Prepare Report
        tempReportFields.append(tempReportField)
        prepareReport(tempReportFields)
