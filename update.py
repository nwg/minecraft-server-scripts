#!/usr/bin/env python3

import os
import time
import shutil
import hashlib
import time
from datetime import datetime
import logging
import requests
import subprocess
import sys

# CONFIGURATION
UPDATE_TO_SNAPSHOT = True
MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
BACKUP_DIR = 'world_backups'
LOG_FILENAME = 'auto_updater.log'

SERVER_JAR = '../server.jar'

SYSTEMD_SERVICE = 'minecraft.service'

def get_service_pid(servicename):
    result = subprocess.check_output(['/usr/bin/systemctl', 'show', '--user', '--property', 'MainPID', '--value', SYSTEMD_SERVICE]).strip()
    return int(result)

def stop_service(servicename):
    return subprocess.check_output(['/usr/bin/systemctl', '--user', 'stop', servicename])

def start_service(servicename):
    subprocess.check_output(['/usr/bin/systemctl', '--user', 'start', servicename])

def is_service_running(servicename):
    try:
        subprocess.check_output(['/usr/bin/systemctl', '--user', 'status', servicename])
    except CalledProcessError:
        return False
    return True

def send_cmd(pid, cmd):
    stdin = f'/proc/{pid}/fd/0'
    with open(stdin, 'w') as f_stdin:
        f_stdin.write(cmd)

logging.basicConfig(
    filename=LOG_FILENAME,
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# retrieve version manifest
response = requests.get(MANIFEST_URL)
data = response.json()

if UPDATE_TO_SNAPSHOT:
    minecraft_ver = data['latest']['snapshot']
else:
    minecraft_ver = data['latest']['release']

# get checksum of running server
if os.path.exists(SERVER_JAR):
    sha = hashlib.sha1()
    f = open(SERVER_JAR, 'rb')
    sha.update(f.read())
    cur_ver = sha.hexdigest()
else:
    cur_ver = ""

for version in data['versions']:
    if version['id'] == minecraft_ver:
        jsonlink = version['url']
        jar_data = requests.get(jsonlink).json()
        jar_sha = jar_data['downloads']['server']['sha1']

        logging.info('Your sha1 is ' + cur_ver + '. Latest version is ' + str(minecraft_ver) + " with sha1 of " + jar_sha)

        if cur_ver != jar_sha:
            logging.info('Updating server...')
            link = jar_data['downloads']['server']['url']
            logging.info('Downloading .jar from ' + link + '...')
            response = requests.get(link)
            with open('minecraft_server.jar', 'wb') as jar_file:
                jar_file.write(response.content)
            logging.info('Downloaded.')

            pid = get_service_pid('minecraft.service')
            if is_service_running(SYSTEMD_SERVICE):
                send_cmd(pid, 'say ATTENTION: Server will shutdown for 1 minutes to update in 30 seconds.')
                logging.info('Shutting down server in 30 seconds.')

                for i in range(20, 9, -10):
                    time.sleep(10)
                    send_cmd(pid, f'say Shutdown in {i} seconds')

                for i in range(9, 0, -1):
                    time.sleep(1)
                    send_cmd(pid, f'say Shutdown in {i} seconds')
                time.sleep(1)

                logging.info('Stopping server.')
                stop_service(SYSTEMD_SERVICE)
                time.sleep(5)

            logging.info('Backing up world...')

            if not os.path.exists(BACKUP_DIR):
                os.makedirs(BACKUP_DIR)

            backupPath = os.path.join(
                BACKUP_DIR,
                "world" + "_backup_" + datetime.now().isoformat().replace(':', '-') + "_sha=" + cur_ver)
            shutil.copytree("../world", backupPath)

            logging.info('Backed up world.')
            logging.info('Updating server .jar')

            if os.path.exists(SERVER_JAR):
                os.remove(SERVER_JAR)

            os.rename('minecraft_server.jar', SERVER_JAR)
            logging.info('Starting server...')
            start_service(SYSTEMD_SERVICE)

        else:
            logging.info('Server is already up to date.')

        break

