import toml
import subprocess
import time
from notify import startGUI
import sys
import os
import shutil

class Task:
    def __init__(self, server, finished, ssh_cmd, target_cmd):
        self.server = server
        self.finished = finished
        self.ssh_cmd = ssh_cmd
        self.target_cmd = target_cmd

def get_sshpass_path():
    if getattr(sys, 'frozen', False):
        # When bundled, sshpass will be in the root of the extracted resources
        base_path = sys._MEIPASS
    else:
        # When running as script, look in project root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    sshpass_path = os.path.join(base_path, 'sshpass.exe')
    if os.path.isfile(sshpass_path):
        return sshpass_path
    if shutil.which('sshpass'):
        return 'sshpass'
    raise FileNotFoundError("sshpass.exe not found in application root or system PATH")

def load_config(config_path):
    """Load and validate the TOML configuration file."""
    with open(config_path, 'r') as f:
        config = toml.load(f)
    servers = config['target']['servers']
    required_keys = ['ip', 'port', 'password', 'passPrompt', 'username', 'targetCmd']
    for server in servers:
        for key in required_keys:
            if key not in config[server]:
                raise KeyError(f"Missing required key in config[{server}]: {key}")
    
    try:
        for server in servers:
            config[server]['port'] = int(config[server]['port'])
    except ValueError:
        raise ValueError("Port must be an integer.")
    
    return config

def check_all_done(tasks):
    for task in tasks:
        if not task.finished:
            return False
    sys.exit(0)

def main():
    # Configuration file handling
    config_path = 'config.toml'
    if not os.path.isfile(config_path):
        print(f"Error: Config file '{config_path}' not found.")
        input("Press any key to exit...")
        sys.exit(1)
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        input("Press any key to exit...")
        sys.exit(1)
    
    # SSHPass path resolution
    try:
        sshpass_path = get_sshpass_path()
    except FileNotFoundError as e:
        print(e)
        input("Press any key to exit...")
        sys.exit(1)

    tasks = []
    for server in config['target']['servers']:
        
    # Build the SSH command
        ssh_cmd = [
            sshpass_path,
            '-p', config[server]['password'],
            '-P', config[server]['passPrompt'],
            'ssh',
            '-p', str(config[server]['port']),
            f"{config[server]['username']}@{config[server]['ip']}",
            '-t',
            f"ps -e | grep '{config[server]['targetCmd']}'"
        ]
        tasks.append(Task(server=server, finished=False, ssh_cmd=ssh_cmd, target_cmd=config[server]['targetCmd']))
    # Main monitoring loop
    while True:
        for task in tasks:
            if task.finished:
                continue
            print(f"Checking {task.server} with command: {' '.join(task.ssh_cmd)}")
            try:
                result = subprocess.run(
                    task.ssh_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
            except subprocess.TimeoutExpired:
                print(f"On {task.server}, SSH command timed out. Retrying in 10 seconds...")
                continue
            if result.returncode != 0:
                print(f"On {task.server}, SSH error (code {result.returncode}): {result.stderr.strip()}. Retrying in 10 seconds...")
                continue
            if result.stdout.find(task.target_cmd) != -1:
                print(f"On {task.server}, {task.target_cmd} found. Next check in 10 seconds...")
                continue
            print(f"On {task.server}, {task.target_cmd} not found. Sending notification.")
            startGUI(task.server)
            task.finished = True
        check_all_done(tasks)
        time.sleep(10)
if __name__ == '__main__':
    main()