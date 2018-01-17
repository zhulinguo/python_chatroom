# -*- coding:utf-8 -*-
import socket
import sys
import threading
import client_data_process
import struct
import select
import json

header_len = 4

#############################################################
###本文件负责服务器socket相关工作
#############################################################

if __name__ == "__main__":
    sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('192.168.1.136', 10000)
    while True:
        try:
            ret = sock_fd.connect(server_address)
            client_data_process.SOCK_FD = sock_fd
            print "Connect success!"
            break
        except:
            print 'Connected faild, reconnecting...'

    #############################################################
    ###必须先登陆才能进行之后的聊天，可以选择注册
    #############################################################
    while True:
        print "Please select the following numbers:"
        print "  1.register  2.login"
        input = sys.stdin.readline().strip('\n')
        try:
            input = int(input)
        except:
            print "******Please '1' or '2'!"
            continue
        if 1 == input:
            client_data_process.do_register()
            continue
        elif 2 == input:
            ret = client_data_process.do_login()
            if ret:
                break

    #############################################################
    ###创建新的线程监视控制台输入的信息
    #############################################################
    t = threading.Thread(target=client_data_process.wait_input)
    t.setDaemon(True)
    t.start()

    inputs = [sock_fd]
    while True:
        readable, writeable, exceptional = select.select(inputs, [], [])
        for event in inputs:
            data_buffer = bytes()
            while True:
                data = event.recv(1024)
                if data:
                    data_buffer += data
                    if len(data_buffer) < header_len:
                        continue
                    body_size = struct.unpack('i', data_buffer[:header_len])[0]
                    if len(data_buffer) < header_len + body_size:
                        continue
                    data = data_buffer[header_len:header_len + body_size]
                    data = data.decode()
                    data = json.loads(data)
                    ret = client_data_process.decode(data)
                    if len(data_buffer) == header_len + body_size:
                        break
                    else:
                        data_buffer = data_buffer[header_len + body_size:]
                else:
                    print "disconnected..."
                    inputs.remove(event)
                    break