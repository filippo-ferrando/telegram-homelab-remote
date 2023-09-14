# Telegram bot that allows to launch ansible playbooks on remote hosts
# Also allows the admin to know if the ups is on battery mode or not

# FEATURES:
# - Launch ansible playbooks on remote hosts    :tick
# - Know if the ups is on battery mode or not   :tick
# - Know if the hosts are up or not             :tick
# - Launch custom command on selected host      :tick
#
# - Docker generic -> info about runners and containers 

# Thinking about using the same way of launching remote command (or playbooks) to control docker containers
# Using ansible_runner the docker lib is not necessary, but it will be used for other things
import time
from os.path import exists
import subprocess
import logging

# Ansible lib
import ansible_runner


# Docker lib
import docker


# Importing the telepot library
import telepot


# Importing the token file
with open('TOKEN.txt', 'r') as token_file:
    TOKEN = token_file.read().replace('\n', '')

global CHAT_ID

# Version 0.1 will be able to launch ansible playbooks on remote hosts

# pass a host is unnecessary, the playbook will do it in the hosts section of the yaml file
def playbook_runner(playbook_name):
        r = ansible_runner.run(private_data_dir='/.ansible/playbooks', playbook=playbook_name) # -> not the definitive path but for now it will do
        #print("{}: {}".format(r.status, r.rc))
        return r.status, r.rc # -> this will return the status and the return code of the playbook

def check_ups_battery(self):
    global CHAT_ID
    # controll if .ups_battery.alert exists
    if(exists("/.ups_battery.alert")):
        # send text to admin
        self.bot.sendMessage(CHAT_ID, "Ups battery mode on, sending shutdown command to all hosts")
        # send shutdown command to all hosts
        status, rc = playbook_runner("shutdown_ups.yml")
        msg_return = "Status: " + status + "\nReturn code: " + rc
        self.bot.sendMessage(CHAT_ID, msg_return)
        # delete .ups_battery.alert
        subprocess.check_output("rm /.ups_battery.alert", shell=True, stderr=subprocess.STDOUT)
    else:
        pass


def ups_control():
        # Control if ups_battery.alert exists
            #if so return battery mode on
            # else return normal state
        if(exists("/.ups_battery.alert")):
            return "battery mode on"
        else:
            return "normal state"

def host_up_controll():
    # use a host file and send a ping
    with open(".hosts.txt", "r") as host_file:
        host_list = host_file.read().split("\n")
    responses = {}
    for host in host_list:
        responses[host] = subprocess.check_output(f"ping -c 1 {host}", shell=True, stderr=subprocess.STDOUT)

    return responses

def custom_command_runner(host, command): #not much but works so far
    # structure of the command
        # sudo ansible <host/group> -m shell -a "<command>"
    response = subprocess.check_output(f"ansible {host} -m shell -a {command}", shell=True, stderr=subprocess.STDOUT) # not the best way but using ansible is easier than paramiko in this case
    return response

class TelegramBot:
    def __init__(self, bot_token):
        self.bot = telepot.Bot(bot_token)
        self.logger = logging.getLogger('TelegramBot')
        self.logger.setLevel(logging.INFO)
        self.setup_logger()
    
    def setup_logger(self):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Log to console
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
    
    def handle_message(self, msg):
        global CHAT_ID
        content_type, chat_type, chat_id = telepot.glance(msg)
        CHAT_ID = chat_id
        message = msg['text'].split(" ")
        if(message[0] == "/run"):
            status, rc = playbook_runner(f"{message[1]}.yml")
            msg_return = "Status: " + status + "\nReturn code: " + rc
            self.bot.sendMessage(chat_id, msg_return)
        elif(message[0] == "/battery"):
            response = ups_control()
            self.bot.sendMessage(chat_id, response)
        elif(message[0] == "/up"):
            reponses = host_up_controll()
            self.bot.sendMessage(chat_id, reponses)
        elif(message[0] == "/command"):
            msg = custom_command_runner(message[1], f"'{message[2]}'")     
            self.bot.sendMessage(chat_id, msg)
    
    def start(self):
        self.bot.message_loop(self.handle_message)
        self.logger.info('Bot is listening...')
        while True:
            try:
                time.sleep(1800)
                check_ups_battery(self) # -> this will work as a listener for the ups battery activity
            except KeyboardInterrupt:
                self.logger.info('Bot stopped')
                exit()

if __name__ == '__main__':
    bot = TelegramBot(TOKEN)
    bot.start()
