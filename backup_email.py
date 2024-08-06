from netmiko import ConnectHandler
import os
import datetime
import logging
import smtplib
from email.mime.text import MIMEText
import ssl

# Set up logging
logging.basicConfig(
    filename='/var/log/netmiko_backup.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Read the router information from the /etc/hosts_backup file
def read_router_info(hosts_file="/etc/hosts_backup"):
    routers = []
    with open(hosts_file, 'r') as file:
        for line in file:
            if not line.startswith('#'):
                parts = line.strip().split()
                if len(parts) >= 2:
                    ip = parts[0]
                    router = {
                        'device_type': 'juniper_junos',
                        'ip': ip,
                        'username': os.getenv('USERNAME'),
                        'password': os.getenv('PASSWORD'),
                    }
                    routers.append(router)
    return routers

# Connect to each router and save the configuration
def save_router_configuration(routers, backup_directory):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = os.path.join(backup_directory, timestamp)
    os.makedirs(backup_folder, exist_ok=True)
    logging.info(f'Created backup directory: {backup_folder}')

    for router in routers:
        try:
            logging.info(f'Connecting to router: {router["ip"]}')
            connection = ConnectHandler(**router)
            hostname_output = connection.send_command('show version | match hostname')
            hostname = hostname_output.split(":")[1].strip().split()[0]
            logging.info(f'Saving configuration for router: {hostname}')
            output = connection.send_command('show configuration')
            connection.disconnect()

            # Save the configuration to a text file
            file_path = os.path.join(backup_folder, f'{hostname}.txt')
            with open(file_path, 'w') as file:
                file.write(output)

            logging.info(f'Successfully saved the configuration for {hostname}.')

        except Exception as e:
            logging.error(f'Failed to connect to {router["ip"]}. Error: {str(e)}')

    # Send email notification
    send_email(backup_folder)

def send_email(backup_folder):
    sender = 'dfeluduxyz@gmail.com'
    recipients = ['daniel.feludu@wiocc.net', 'george.cheng@wiocc.net']
    subject = 'Router Configuration Backup Completed'
    body = f'The router configuration backup has been completed and stored in the following directory:\n\n{backup_folder}'

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, '')
            smtp.send_message(msg)
        logging.info('Email notification sent successfully.')
    except Exception as e:
        logging.error(f'Failed to send email notification. Error: {str(e)}')

# Main code
if __name__ == '__main__':
    backup_directory = os.path.join('/', 'backup_config')
    if not os.path.exists(backup_directory):
        os.makedirs(backup_directory)
        logging.info(f'Created backup directory: {backup_directory}')
    routers = read_router_info()
    save_router_configuration(routers, backup_directory)
