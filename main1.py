import sys
import threading
import socket
from logger import Logger
from server1 import FTPServer

try:
    HOST = socket.gethostbyname(socket.gethostname( ))
except socket.gaierror:
    HOST = '127.0.0.1'

PORT = None
logger = None

def serverListener( ):
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((HOST, PORT))
    listen_sock.listen(5)

    logger.write_to_log_file('Started server on ' + HOST + ':' + str(PORT))
    while True:
        connection, address = listen_sock.accept( )
        f = FTPServer(connection, address, HOST, PORT, FILE_NAME)
        f.start()
        logger.write_to_log_file('Connected on ' + address[0] + ':' + str(address[1]))


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        print("Please give log filename and port number")
        exit()

    FILE_NAME = args[1] 
    PORT = int(args[2])
    logger = Logger(FILE_NAME)

    listener = threading.Thread(target=serverListener)
    listener.start( )