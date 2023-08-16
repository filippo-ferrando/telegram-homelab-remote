# Telegram bot that allows to launch ansible playbooks on remote hosts
# Also allows the admin to know if the ups is on battery mode or not

# FEATURES:
# - Launch ansible playbooks on remote hosts    :tick
# - Know if the ups is on battery mode or not
# - Know if the hosts are up or not             :tick
# - Launch custom command on selected host      :tikck

import time
import os
import subprocess
import ansible_runner
import logging

# Importing the telepot library

import telepot

# Importing the token file
with open('TOKEN.txt', 'r') as token_file:
    TOKEN = token_file.read().replace('\n', '')

# Version 0.1 will be able to launch ansible playbooks on remote hosts

def playbook_runner(playbook_name):
        r = ansible_runner.run(private_data_dir='/tmp/', playbook=playbook_name)
        print("{}: {}".format(r.status, r.rc))
        return r.status, r.rc

def ups_control():
        # Control if ups_battery.alert exists
            #if so return battery mode on
            # else return normal state
        pass

def host_up_controll():
    # use a host file and send a ping
    with open(".hosts.txt", "r") as host_file:
        host_list = host_file.read().split("\n")
    responses = {}
    for host in host_list:
        responses[host] = subprocess.check_output(f"ping -c 1 {host}", shell=True)

    return responses

def custom_command_runner(host, command):
    # using ansible because why not
    # structure of the command
        # sudo ansible <host/group> -m shell -a "<command>"
    response = subprocess.check_output(f"sudo ansible {host} -m shell -a {command}", shell=True)
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
        content_type, chat_type, chat_id = telepot.glance(msg)
        message = msg['text'].split(" ")
        if(message[0] == "/run"):
            status, rc = playbook_runner(message[1])
            msg_return = "Status: " + status + "\nReturn code: " + rc
            self.bot.sendMessage(chat_id, msg_return)
        elif(message[0] == "/battery"):
            #Call ups control function
            pass
        elif(message[0] == "/up"):
            reponses = host_up_controll()
            self.bot.sendMessage(chat_id, reponses)
        elif(message[0] == "/command"):
            msg = custom_command_runner(message[1], message[2])     
            self.bot.sendMessage(chat_id, msg)
    
    def start(self):
        self.bot.message_loop(self.handle_message)
        self.logger.info('Bot is listening...')
        while True:
            try:
                time.sleep(10)
                # check_ups_battery() -> this will work as a listener for the ups battery activity
            except KeyboardInterrupt:
                self.logger.info('Bot stopped')
                exit()

if __name__ == '__main__':
    bot = TelegramBot(TOKEN)
    bot.start()
