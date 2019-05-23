import socket
import threading
import os
import stat
import sys
import time
from logger import Logger
from server import Server

try:
    HOST = socket.gethostbyname(socket.gethostname( ))
except socket.gaierror:
    HOST = '127.0.0.1'
PORT = 21  # command port

logger = None
FILE_NAME = None

def intialize_server():
    listening_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listening_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listening_sock.bind((HOST, PORT))
    listening_sock.listen(5)

    logger.write_to_log_file('Listening on host ' + HOST)

    while True:
        connection, address = listening_sock.accept()
        server_each = Server(connection, address, FILE_NAME)
        server_each.start()
        logger.write_to_log_file('Connected on ' + address[0] + ":" + str(address[1]))


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        print("Please give log filename and port number")
        exit()
    FILE_NAME = args[1] 
    PORT = int(args[2])
    logger = Logger(FILE_NAME)
    server = threading.Thread(target=intialize_server)
    server.start()

