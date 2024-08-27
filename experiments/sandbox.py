## Sandbox.py
# @author jcpoir

import sys
import subprocess

def run(command):
    ''' run the specified command via subprocess.run '''
    command = command.split(" ")

    subprocess.run(command)

command = ""
for game in range(0, 16):
    command += f'python3 api_import.py {game} & \n'
command += " wait"

print(command)

run(command)