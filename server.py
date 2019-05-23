#!/usr/bin/env python3
import sys
import threading
import socket
from logger import Logger

CLRF = '\r\n'
STATUS_CODE_220 = '220'

class Server(threading.Thread):
    def __init__(self, cmd_sock, address, file_name):
        threading.Thread.__init__(self)
        self.cmd_sock = cmd_sock
        self.address = address
        self.logger = Logger(file_name)

    def run(self):
        """
        receive commands from client and execute commands
        """
        self.welcome_msg()
        """
        while True:
            try:
                data = self.cmd_sock.recv(1024).rstrip()
                try:
                    cmd = data.decode('utf-8')
                except AttributeError:
                    cmd = data
                self.logger.write_to_log_file('Received data')
                if not cmd:
                    break
            except socket.error as err:
                self.logger.write_to_log_file('Receive')

            try:
                cmd, arg = cmd[:4].strip().upper(), cmd[4:].strip( ) or None
                func = getattr(self, cmd)
                func(arg)
            except AttributeError as err:
                self.sendCommand('500 Syntax error, command unrecognized. '
                    'This may include errors such as command line too long.\r\n')
                self.logger.write_to_log_file('Receive')
        """

    def send_cmd(self, cmd):
        self.cmd_sock.send(cmd.encode('utf-8'))

    def send_data(self, data):
        self.data_sock.send(data.encode('utf-8'))

    def welcome_msg(self):
        self.send_cmd(f"{STATUS_CODE_220} Welcome to my server")