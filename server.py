#!/usr/bin/env python3

import socket
import threading
import os
import stat
import sys
import time
import subprocess
from logger import Logger
from dfa import DFA

allow_delete = False
BLOCK=8192
CRLF = '\r\n'

status_code = {
    150: '150 File status okay; about to open data connection.',
    221: '221 Service closing control connection',
    226: '226 Closing data connection. Requested file action successful (for example, file transfer or file abort).',
    230: '230 User logged in, proceed. Logged out if appropriate',
    331: '331 User name okay, need password',
    430: '430 Invalid username or password',
    501: 'Syntax error in parameters or arguments.',
    502: '502 Command not implemented.',
    503: 'Bad sequence of commands.',
    530: '530 Not logged in',
    550: 'Requested action not taken. File unavailable (e.g., file not found, no access).'
}

class FTPServer(threading.Thread):
    def __init__(self, cmd_sock, address, host, port, file_name):
        threading.Thread.__init__(self)
        self.pwd = os.getenv('HOME')
        self.cmd_sock = cmd_sock
        self.address = address
        self.host = host
        self.port = port
        self.data_mode = 'A'
        self.logger = Logger(file_name)
        self.logged_in = False
        self.is_active = True
        self.dfa = DFA()
        self.__user_dict = self.__get_user()

    def __get_user(self):
        """
        Populate user dictionary from account file. Private to keep secured
        """
        user_dict = dict()
        with open('./accounts.txt') as f:
            users = f.readlines()

        for x in users:
            user = x.strip().split(' ')
            username, password = user
            user_dict[username] = password
        
        return user_dict

    def run(self):
        """
        Start each thread and receive command to excecute
        This dynamically choose function to excecute based on the command 
        """
        self.welcome()

        while True:
            try:
                data = self.cmd_sock.recv(1024).rstrip()
                try:
                    response = data.decode('utf-8')
                    self.logger.write_to_log_file("RECEIVED " + str(response) + "\n")
                except :
                    response = data
                if not response:
                    break
                cmd = response[:4].strip().upper()
                arg = None
                if (len(response) > 4):
                    arg = response[4:].strip()
                method = getattr(self, cmd)
                method(arg)
            except:
                self.send_cmd(status_code[503] + CRLF)


    def send_cmd(self, cmd):
        """
        Send command back to client
        """
        self.logger.write_to_log_file("SENT: " + cmd)
        self.cmd_sock.send(cmd.encode('utf-8'))

    def send_data(self, data):
        """
        Send data to client
        I could log the data here but seems like unecessary
        """
        if self.data_mode == 'A':
            self.data_sock.send(data.encode('utf-8'))
        else:
            self.data_sock.send(data)

    def open_data_sock(self):
        """
        Open the data connection to get data
        Dynmically create or connect to socket depends on which mode PASV OR PORT
        """
        try:
            self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #PORT: connect to client
            if self.is_active:
                self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.data_sock.connect((self.data_sock_addr, self.data_sock_port))
            #PASV: receive connection
            else:
                self.data_sock, self.address = self.sock.accept()
        except socket.error as error:
            logger.write_to_log_file(str(error))

    def close_data_sock(self):
        """
        Close the data socket when done getting data
        """
        try:
            if not self.is_active:
                self.sock.close()
            self.data_sock.close()
        except socket.error as error:
            logger.write_to_log_file(str(error))

    def welcome(self):
        """
        Send welcome message to client
        """
        self.send_cmd('220 Welcome to this server.' + CRLF)

    def SYST(self, command):
        """
        Send system information
        """
        self.send_cmd(f"215 {sys.platform} type.{CRLF}")
    
    def CWD(self, path):
        """
        Change working directory by setting the pwd variable
        """        
        full_path = path.endswith(os.path.sep) and path or os.path.join(self.pwd, path)
        try:
            self.pwd = full_path
            self.send_cmd('250 Changed directory successfuly.' + CRLF)
        except:
            self.send_cmd(status_code[550] + CRLF)

    def CDUP(self, command):
        """
        Change up one directory
        """
        self.pwd = os.path.abspath(os.path.join(self.pwd, '..'))
        self.send_cmd('250 Changed directory successfuly.' + CRLF)

    def PWD(self, command):
        """
        Send current working directory path
        """
        self.send_cmd(f"257 {self.pwd}.{CRLF}")

    def QUIT(self, command):
        """
        Close connection
        """
        #Important for security reason
        self.logged_in = False
        self.send_cmd('221 Service clsing connection. Goodbye!' + CRLF)
    
    def USER(self, user):
        """
        Validate user and send appropriate messsage back
        """
        if user not in self.__user_dict:
            self.send_cmd(status_code[430] + CRLF)
        else:
            self.send_cmd(status_code[331] + CRLF)
            self.user = user

    def PASS(self, password):
        """
        Validate password and send appropriate messsage back
        """
        if self.__user_dict[self.user] != password:
            self.send_cmd(status_code[430] + CRLF)
        else:
            self.send_cmd(status_code[230] + CRLF)
            self.logged_in = True

    def TYPE(self, type):
        self.data_mode = type
        if self.data_mode == 'A':
            self.send_cmd('200 ASCII active' + CRLF)
        elif self.data_mode == 'I':
            self.send_cmd('200 Binary active' + CRLF)

    def PASV(self, command):
        """
        Send the address and port content for the client to connect to
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, 0))
            self.sock.listen(5)
            addr, port = self.sock.getsockname()
            addr_to_send = ','.join(addr.split('.'))
            port_to_send_1 = port>>8&0xFF
            port_to_send_2 = port&0xFF
            self.send_cmd(f'227 Entering Passive Mode ({addr_to_send},{port_to_send_1},{port_to_send_2}).{CRLF}')
            self.is_active = False
        except:
            self.logger.write_to_log_file("Cannot enter passive mode")
            self.send_cmd(status_code[502] + CRLF)

    def PORT(self, command):
        """
        Set the addr and port for the data sock to connect to
        Close the passive connection if necessary
        """
        try:
            if not self.is_active:
                self.sock.close()
                self.is_active = True
            connection_info = command.split(',')
            self.data_sock_addr = '.'.join(connection_info[:4])
            self.data_sock_port = (int(connection_info[4])<<8) + int(connection_info[5])
            self.send_cmd('200 Received connection info. Entering active mode' + CRLF)
        except:
            self.logger.write_to_log_file("Cannot enter active mode")
            self.send_cmd(status_code[502] + CRLF)

    def EPSV(self, command):
        """
        This should work for any protocol
        Send the address and port content for the client to connect to
        """
        try:
            self.sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.sock.bind((self.host, 0))
            self.sock.listen(5)
            addr, port = self.sock.getsockname()
            addr_to_send = ','.join(addr.split('.'))
            self.send_cmd(f'229 Entering Extended Passive Mode (|||{port}|){CRLF}')
            self.is_active = False
        except:
            self.logger.write_to_log_file("Cannot enter extended passive mode")
            self.send_cmd(status_code[502] + CRLF)

    def EPRT(self, command):
        """
        This should work for any protocol
        Set the addr and port for the data sock to connect to
        Close the passive connection if necessary
        """
        try:
            if not self.is_active:
                self.sock.close()
                self.is_active = True
            connection_info = command.split(',')
            self.data_sock_addr = '.'.join(connection_info[:4])
            self.data_sock_port = (int(connection_info[4])<<8) + int(connection_info[5])
            self.send_cmd('200 Received connection info. Entering active mode' + CRLF)
        except:
            self.logger.write_to_log_file("Cannot enter active mode")
            self.send_cmd(status_code[502] + CRLF)

    def LIST(self, path):
        """
        List the file of the current working directory by default
        If a path is specified, list the content of that path
        """
        #Check if authenticated
        if not self.logged_in:
            self.send_cmd(status_code[530] + CRLF)
            return

        if path:
            #Get full path
            full_path = path.endswith(os.path.sep) and path or os.path.join(self.pwd, path)
            # define the ls command
            ls = subprocess.Popen(["ls", "-l", str(full_path)],  
                                stdout=subprocess.PIPE,
                                )
        else:
            ls = subprocess.Popen(["ls", "-l", self.pwd],  
                                stdout=subprocess.PIPE,
                                )

        self.open_data_sock()
        self.send_cmd(status_code[150] + CRLF)
        # output the files line by line
        for line in ls.stdout:  
            self.send_data(line.decode('utf-8'))
        self.close_data_sock()
        self.send_cmd(status_code[226] + CRLF)

    def RETR(self, file_name):
        """
        Retrive files usually in binary mode
        """
        #Check if user is authenticated
        if not self.logged_in:
            self.send_cmd(status_code[530] + CRLF)
            return

        full_path = os.path.join(self.pwd, file_name)
        f = None

        try:
            if self.data_mode == 'A':
                f = open(full_path, 'r')
            else:
                f = open(full_path, 'rb')
        except:
            self.send_cmd(status_code[550] + CRLF)
            return

        self.send_cmd(status_code[150] + CRLF)
        self.open_data_sock()

        #Read data line by line
        while True:
            block = f.read(BLOCK)
            if not block:
               break 
            self.send_data(block)

        self.close_data_sock()
        self.send_cmd(status_code[226] + CRLF)
        f.close()

    def STOR(self, file_name):
        """
        Upload file to client
        """
        if not self.logged_in:
            self.send_cmd(status_code[530] + CRLF)
            return

        full_path = os.path.join(self.pwd, file_name)
        f = None

        try:
            if self.data_mode == 'A':
                f = open(full_path, 'w')
            else:
                f = open(full_path, 'wb')
        except:
            self.send_cmd(status_code[550] + CRLF)
            return

        self.send_cmd(status_code[150] + CRLF)
        self.open_data_sock()

        while True:
            block = self.data_sock.recv(BLOCK)
            if not block:
               break 
            f.write(block)

        self.close_data_sock()
        self.send_cmd(status_code[226] + CRLF)
        f.close()