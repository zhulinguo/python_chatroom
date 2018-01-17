# -*- coding:utf-8 -*-
import socket
import select
import json
import threading
import server_data_process
import struct

header_len = 4

#############################################################
###本文件负责服务器socket相关工作
#############################################################

if __name__ == "__main__":
    server_data_process.init()
    sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('', 10000)
    sock_fd.bind(server_address)
    sock_fd.listen(100)
    print "server listen start : ", server_address

    #############################################################
    ###创建一个线程用于定时向每个聊天室发送21点游戏题目
    #############################################################
    t = threading.Thread(target=server_data_process.game_timer)
    t.setDaemon(True)
    t.start()

    server_data_process.INPUTS = [sock_fd]

    #############################################################
    ###将接收队列放进select中进行监听
    #############################################################
    while True:
        readable, writeable, exceptional = select.select(server_data_process.INPUTS, [], [])
        for connection in readable:
            if connection is sock_fd:
                cli_fd, cli_addr = connection.accept()
                print "get connection from : ", cli_addr
                cli_fd.setblocking(False)
                cli_fd.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                server_data_process.INPUTS.append(cli_fd)                      #每次accept就将新的连接加入select监听的队列
            else:
                data_buffer = bytes()
                while True:
                    try:
                        data = connection.recv(1024)
                    except:
                        server_data_process.clear_sock(connection)             #连接发生异常时清除错误连接
                        break
                    if data:
                        ##################################################################
                        ###考虑到TCP分包的情况，对其进行粘包
                        ###每次先解析出头部4个字节，查看包的大小，直到接收到足够多长度再进行数据解析
                        ##################################################################
                        data_buffer += data
                        if len(data_buffer) < header_len:
                            continue
                        body_size = struct.unpack('i', data_buffer[:header_len])[0]
                        if len(data_buffer) < header_len + body_size:
                            continue
                        data = data_buffer[header_len:header_len+body_size]
                        message = data.decode()
                        message = json.loads(message)
                        ret = server_data_process.decode(message, connection)
                        if len(data_buffer) == header_len+body_size:
                            break
                        else:
                            data_buffer = data_buffer[header_len+body_size:]
                    else:
                        server_data_process.clear_sock(connection)              #客户端主动断开，清除连接
                        break