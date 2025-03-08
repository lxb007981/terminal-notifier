import toml
import subprocess
import time
from plyer import notification
import sys
import os
import shutil

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
    
    required_keys = ['ip', 'port', 'password', 'passPrompt', 'username', 'targetCmd']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required key in config: {key}")
    
    try:
        config['port'] = int(config['port'])
    except ValueError:
        raise ValueError("Port must be an integer.")
    
    return config

def main():
    # Configuration file handling
    config_path = 'config.toml'
    if not os.path.isfile(config_path):
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)
    
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    # SSHPass path resolution
    try:
        sshpass_path = get_sshpass_path()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    
    # Build the SSH command
    ssh_cmd = [
        sshpass_path,
        '-p', config['password'],
        '-P', config['passPrompt'],
        'ssh',
        '-p', str(config['port']),
        f"{config['username']}@{config['ip']}",
        '-t',
        f"ps -e | grep '{config['targetCmd']}'"
    ]
    
    # Main monitoring loop
    while True:
        try:
            result = subprocess.run(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
        except subprocess.TimeoutExpired:
            print("SSH command timed out. Retrying in 10 seconds...")
            time.sleep(10)
            continue
        if result.returncode != 0:
            print(f"SSH error (code {result.returncode}): {result.stderr.strip()}. Retrying in 10 seconds...")
            time.sleep(10)
            continue
        if result.stdout.find(config['targetCmd']) != -1:
            print("Process found. Next check in 10 seconds...")
            time.sleep(10)
            continue
        
        print("Process not found. Sending notification and exiting.")
        try:
            notification.notify(
                title='Process Not Found',
                message='The target process is no longer running.',
                app_name='terminal notifier',
                timeout=10
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")
        break

if __name__ == '__main__':
    main()