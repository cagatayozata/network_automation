<div align="center">
  <h3 align="center">Network Device Configuration Automation</h3>
</div>
<p align="center">
 <img width="300" height="300" src="https://user-images.githubusercontent.com/36114345/235368861-a874d80c-7b6b-4cfb-b6d2-917db721bd83.png">
</p>
<br />


<!-- TABLE OF CONTENTS -->
  ## Table of Contents
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ABOUT THE PROJECT -->
## About The Project


https://user-images.githubusercontent.com/36114345/235368745-f74a9b6c-9239-422f-9fb8-44517954fa68.mov


The Network Device Configuration Automation Project automates the process of changing IP addresses on network devices. Nautobot is used as the source of truth (SoT) and the changes are applied to the devices via Restconf API.

* Retrieve device connection information from a trusted source of truth (SoT) such as Nautobot, including device name, type, role, interface name, type, and IP address.
* Validate the retrieved data based on pre-defined rules.
* Compare the information obtained from Nautobot with the current configuration of the device.
* Modify the configuration of network devices using the Restconf API endpoints.
* Generate a summary CSV report for the changes made to the device configurations.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Prepare a Python Development Environment

We recommend you to install latest Python and pip on your system.

A Python virtual environment is also highly recommended.

* [https://docs.python.org/3/tutorial/venv.html](Install a virtual env for Python 3)

### Installation

1. Install python libraries:
   ```sh
   pip3 install -r requirements.txt
   ```
2. Add .env and update file:
   ```sh
   mv .env.example .env
   ```
   ```sh
    # Nautobot
    NAUTOBOT_TOKEN = ""
    NAUTOBOT_API = ""

    # Device
    DEVICE_IP = ""
    DEVICE_PORT = ""
    DEVICE_USERNAME = ""
    DEVICE_PASSWORD = ""
     ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

### Run pyhton file:
 ```sh
 python3 main.py
 ```
When the Python script is executed, the configurations obtained from Nautobot are compared with the interface/IP information on the device. During this process, data validation is applied. If the IP address information retrieved from the interface in Nautobot is different from that in the device configuration, user approval is requested. Upon user approval, the Restconf API is used to update the device configuration.


### Run pyhton file (force mode):
 ```sh
 python3 main.py
 ```
With the force mode enabled, all changes are automatically applied without being presented to the user for approval.
   
### Report Feature

<img width="1141" alt="Screenshot 2023-04-30 at 17 52 11" src="https://user-images.githubusercontent.com/36114345/235368789-3a8d7f8f-23f0-4420-8858-7c8c54588d6d.png">

The Python code automatically generates a .csv report file in the directory where the code is executed each time it is run. The report contains the device name, role, interface name, interface type, IP address retrieved from Nautobot, IP address obtained from the device, and information about the action performed. The file name is created with the current date and time.

### Validation Rules:
 ```sh
        {
            "role": "distribution",
            "regex": "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$",
            "text": "ip_address"
        }
 ```

The default validation rules can be edited through the "rules.json" file. The "role" parameter specifies the device types to which the rule will apply and works with the device types selected in Nautobot.

The relevant regex pattern must be entered into the "regex" parameter and the name of the rule must be entered into the "text" field.

To activate the rules, the "validateData(deviceRole, variable, data)" function should be called in the relevant section of the "main.py" file. The "deviceRole" parameter should be the device type, "variable" should be the name of the rule, and "data" should be the data to be validated.   
   
<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Çağatay ÖZATA - [https://www.linkedin.com/in/cagatayozata/](https://www.linkedin.com/in/cagatayozata/) - mail@cagatayozata.com

Project Link: [https://github.com/your_username/repo_name](https://github.com/your_username/repo_name)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
