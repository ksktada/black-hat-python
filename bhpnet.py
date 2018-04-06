# -*- coding: utf-8 -*-

import sys
import socket
import getopt
import threading
import subprocess

# define global variables
listen = False
command = False
upload = False
execute = ''
target = ''
upload_destination = ''

def usage():
  print 'BHP Net Tool'
  print
  print 'Usage: bhpnet.py -t target_host -p port'
  print '-l --listen              - listen on [host]:[port] for'
  print '                           incoming connections'
  print '-e --execute=file_to_run - execute the given file upon'
  print '                           receiving a connection'
  print '-c --command             - initialize a command shell'
  print '-u --upload=destination  - upon receiving connection upload a'
  print '                           file and write to [destination]'
  print
  print
  print 'Examples:  '
  print 'bhpnet.py -t 192.168.0.1 -p 5555 -l -c'
  print 'bhpnet.py -t 192.168.0.1 -p 5555 -l -u c:\\target.exe'
  print 'bhpnet.py -t 192.168.0.1 -p 5555 -l -e \'cat /etc/passwd\''
  print 'echo "ABCDEFGHI" | ./bhpnet.py -t 192.168.11.22 -p 135'
  sys.exit(0)

def main():
  global listen
  global port
  global execute
  global command
  global upload_destination
  global target

  if not len(sys.argv[1:]):
    usage()

  try:
    opts, args = getopt.getopt(
            sys.argv[1:],
            'hle:t:p:cu:',
            ['help', 'listen', 'execute=', 'target', 'port', 'command', 'upload='])
  except getopt.GetoptError as err:
    print str(err)
    usage()

  for o, a in opts:
    if o in('-h', '--help'):
      usage()
    elif o in ('-l', '--listen'):
      listen = True
    elif o in ('-e', '--execute'):
      execute = a
    elif o in ('-c', '--commandshell'):
      command = True
    elif o in ('-u', '--upload'):
      upload_destination = a
    elif o in ('-t', '--target'):
      target = a
    elif o in ('-p', '--port'):
      port = int(a)
    else:
      assert False, 'Unhandled Option'

  # wait connection or 
  if not listen and len(target) and port > 0:
    buffer = sys.stdin.read()

    client_sender(buffer)

  # start connection waiting
  if listen:
    server_loop()

main()

def client_sender(buffer):
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:
    # connect to target host
    client.connect((target, port))

    if len(buffer):
      client.send(buffer)

    while True:
      # wait data from target host
      recv_len = 1
      response = ''

      while recv_len:
        data = client.recv(4096)
        recv_len = len(data)
        response += data

        if recv_len < 4096:
          break

      print response,

      # wait additional input
      buffer = raw_input('')
      buffer += '\n'

      # send data
      client.send(buffer)

  except:
    print '[*] Exception! Exiting.'

    # finish connection
    client.close()

def server_loop():
  global target

  # if ip address is not specified
  # wait connection in all interface
  if not len(target):
    target = '0.0.0.0'

  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  server.bind((target, port))

  server.listen(5)

  while True:
    client_socket, addr = server.accept()

    # start thread process connection from new client
    client_thread = threading.Thread(target=client_handler, args=(client_socket,))
    client_thread.start()

def run_command():
  # delete new line in the end
  command = command.rstrip()

  # execute command and print result
  try:
    output = subprocess.check_out(command, stderr=subprocess.STDOUT, shell=True)
  except:
    output = 'Failed to execute command.\r\n'

  # send output to client
  return output

def client_handler(client_socket):
  global upload
  global execute
  global command

  # confirm fileupload is selected or not
  if len(upload_destination):

    # read all data and write to file selected
    file_buffer = ''

    # continue receving data until received data is end
    while True:
      data = client_socket.recv(1024)

      if len(data) == 0:
        break
      else:
        file_buffer += data

    # write received data to file
    try:
      file_descriptor = open(upload_destinatin, 'wb')
      file_descriptor.write(file_buffer)
      file_descriptor.close()

      # notify succeed or failed to write
      client_socket.send('Successfully saved file to %s\r\n' % upload_destination)

    except:
      client_socket.send('Failed to save file to %s\r\n' % upload_destination)

  # confirm command is selected or not
  if len(execute):

    # execute command
    output = run_command(execute)

    client_socket.send(output)

  # processing in case that shell is selected
  if command:

    # print prompt
    prompt = '<BHP:#>'
    client_socket.send(prompt)

    while True:

      # receive data while receive new line
      cmd_buffer = ''
      while '\n' not in cmd_buffer:
        cmd_buffer += client_socket.recv(1024)

      # get executed result
      response = run_command(cmd_buffer)
      response += prompt

      # send executed result
      client_socket.send(response)

