# -*- codint: utf-8 -*-

import sys
import socket
import threading

def server_loop(local_host, local_port, remote_host, remote_port, receive_first):

  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:
    server.bind((localhost_, local_port))
  except:
    print '[!!] Failed to listen on %s:%d' % (local_host, local_port)

