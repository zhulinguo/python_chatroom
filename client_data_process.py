# -*- coding:utf-8 -*-
import json
import struct
import sys

#############################################################
###本文件负责所有数据处理
#############################################################
USER = ''
ROOM = ''
SOCK_FD = 0
header_len = 4

#############################################################
###注册的处理函数，发送注册请求后阻塞等待回应
#############################################################
def do_register():
    global SOCK_FD
    while True:
        print "your username: "
        user = sys.stdin.readline().strip('\n')
        if len(user) < 6:
            print "Username must be greater than or equal to 6!"
            continue
        if not user.isalnum():
            print "Username can only be composed of numbers and letters!"
            continue
        if not user[0].isalpha():
            print "Username must start with a letter!"
            continue
        break
    while True:
        print "your password: "
        password = sys.stdin.readline().strip('\n')
        if len(password) > 16 or len(password) < 3:
            print "The password length must be greater than 3 and less than!"
            continue
        if ' ' in password:
            print "The password can not contain spaces!"
            continue
        break
    data = {'type':1, 'user':user, 'password':password}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    SOCK_FD.sendall(send_data)

    data_buffer = bytes()
    while True:
        data = SOCK_FD.recv(1024)             #粘包阻塞等待回应
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
            break
    if 1 == data['errorcode']:
        print "register error: username:%s is eixts!" % data['user']
    elif 0 == data['errorcode']:
        print "register success: username:%s" % data['user']
    return

#############################################################
###登陆的处理函数，发送请求后阻塞等待回应
#############################################################
def do_login():
    global USER
    global SOCK_FD
    while True:
        print "your username: "
        user = sys.stdin.readline().strip('\n')
        if len(user) < 6:
            print "Username must be greater than or equal to 6!"
            continue
        if not user.isalnum():
            print "Username can only be composed of numbers and letters!"
            continue
        if not user[0].isalpha():
            print "Username must start with a letter!"
            continue
        break
    while True:
        print "your password: "
        password = sys.stdin.readline().strip('\n')
        if len(password) > 16 or len(password) < 3:
            print "The password length must be greater than 3 and less than 16!"
            continue
        if ' ' in password:
            print "The password can not contain spaces!"
            continue
        break
    data = {'type': 7, 'user': user, 'password': password}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    SOCK_FD.sendall(send_data)

    data_buffer = bytes()
    while True:
        data = SOCK_FD.recv(1024)                       #粘包阻塞等待回应
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
            break
    if 1 == data['errorcode']:
        print "username:%s not exists!" % data['user']
        return False
    elif 2 == data['errorcode']:
        print "password error!"
        return False
    elif 0 == data['errorcode']:
        print "login success: username:%s" % data['user']
        print "*******************************************************"
        USER = data['user']
        return True
    return False

#############################################################
###创建房间请求发送
#############################################################
def create_room():
    global SOCK_FD
    if '' != ROOM:
        print "You are already in the room!"
        return
    while True:
        print "roomname: "
        roomname = sys.stdin.readline().strip('\n')
        if len(roomname) < 6:
            print "Roomname must be greater than or equal to 6!"
            continue
        if not roomname.isalnum():
            print "Rommname can only be composed of numbers and letters!"
            continue
        break
    while True:
        print "room password: "
        password = sys.stdin.readline().strip('\n')
        if len(password) > 16 or len(password) < 3:
            print "The password length must be greater than 3 and less than 16!"
            continue
        if ' ' in password:
            print "The password can not contain spaces!"
            continue
        break
    data = {'type':2, 'user':USER, 'room':roomname, 'password':password}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    try:
        SOCK_FD.sendall(send_data)
    except:
        print "send request error!"
    return

#############################################################
###进入房间请求发送
#############################################################
def enter_room():
    global SOCK_FD
    if '' != ROOM:
        print "You are already in the room!"
        return
    while True:
        print "roomname: "
        roomname = sys.stdin.readline().strip('\n')
        if len(roomname) < 6:
            print "Roomname must be greater than or equal to 6!"
            continue
        if not roomname.isalnum():
            print "Roomname can only be composed of numbers and letters!"
            continue
        break
    while True:
        print "room password: "
        password = sys.stdin.readline().strip('\n')
        if len(password) > 16 or len(password) < 3:
            print "The password length must be greater than 3 and less than 16!"
            continue
        if ' ' in password:
            print "The password can not contain spaces!"
            continue
        break
    data = {'type': 3, 'user': USER, 'room':roomname, 'password': password}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    try:
        SOCK_FD.sendall(send_data)
    except:
        print "send request error!"
    return

#############################################################
###退出房间请求发送
#############################################################
def exit_room():
    global SOCK_FD
    if '' == ROOM:
        print "You have not joined the room!"
        return
    data = {'type': 4, 'user': USER, 'room':ROOM}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    try:
        SOCK_FD.sendall(send_data)
    except:
        print "send request error!"
    return

#############################################################
###发送列表请求，带上全局ROOM告知所在房间
#############################################################
def list_room():
    global SOCK_FD
    global ROOM
    data = {'type':9, 'room': ROOM}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    try:
        SOCK_FD.sendall(send_data)
    except:
        print "send request error!"
    return

#############################################################
###发送房间里面的聊天报文
#############################################################
def room_chat(content):
    global SOCK_FD
    if '' == content:
        return
    data = {'type': 5, 'user': USER, 'room':ROOM, 'content': content}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    try:
        SOCK_FD.sendall(send_data)
    except:
        print "send message error!"
    return

#############################################################
###发送私聊报文
#############################################################
def private_chat():
    global SOCK_FD
    while True:
        print "target username: "
        target = sys.stdin.readline().strip('\n')
        if len(target) < 6:
            print "Username must be greater than or equal to 6!"
            continue
        if not target.isalnum():
            print "Username can only be composed of numbers and letters!"
            continue
        if not target[0].isalpha():
            print "Username must start with a letter!"
            continue
        break
    print "Please input what you want to say:"
    content = sys.stdin.readline().strip('\n')
    content = content.decode('utf8')
    data = {'type': 6, 'user': USER, 'target': target, 'content': content}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    try:
        SOCK_FD.sendall(send_data)
    except:
        print "send message error!"
    return

#############################################################
###处理创建房间的回应报文，如果创建成功则自动属于该房间
#############################################################
def creat_room_rep(data):
    global ROOM
    if 1 == data['errorcode']:
        print "room exixts: roomname:%s" % data['room']
    elif 0 == data['errorcode']:
        ROOM = data['room']
        print "creat room success: roomname:%s" % data['room']
        print "******************************************************"
    return

#############################################################
###处理加入房间的回应报文
#############################################################
def enter_room_rep(data):
    global ROOM
    if 1 == data['errorcode']:
        print "room not exixts: roomname:%s" % data['room']
        print "******************************************************"
    elif 2 == data['errorcode']:
        print "password error!"
    elif 0 == data['errorcode']:
        print "Entered room: %s" % data['room']
        ROOM = data['room']
    return

#############################################################
###处理退出房间的回应报文
#############################################################
def exit_room_rep(data):
    global ROOM
    if 0 == data['errorcode']:
        print "exit room: %s" % data['room']
        print "******************************************************"
        ROOM = ''
    return

#############################################################
###处理列表请求回应报文
###根据报文中的房间信息选择打印内容是房间列表还是成员列表
#############################################################
def list_room_rep(data):
    global ROOM
    if ROOM != data['room']:
        return
    member_list = data['list']
    i = 1
    if '' == data['room']:
        print "Room list:"
        for member in member_list:
            print "%d. %s" % (i, member)
            i = i + 1
    else:
        print "Room member list:"
        for member in member_list:
            print "%d. %s" % (i, member)
            i = i + 1
    print "*******************************************************"
    return

#############################################################
###接收打印房间内其它成员发来的聊天报文
#############################################################
def room_chat_rep(data):
    if USER != data['user']:
        if '' != ROOM:
            print "<%s>%s: %s" % (data['room'], data['user'], data['content'])
        else:
            print "<hell>%s: %s" % (data['user'], data['content'])

#############################################################
###接收打印私聊报文
#############################################################
def private_chat_rep(data):
    if USER == data['user']:
        print "Wrong username!"
        return
    print "****************"
    print "******%s to you: %s" % (data['user'], data['content'])
    print "****************"
    return

#############################################################
###发送自己给出的21点游戏答案
#############################################################
def send_21game_ans():
    global SOCK_FD
    global USER
    global ROOM
    if '' == ROOM:
        print "you are not in the room!"
        return
    else:
        print "please input your answer:"
    ans = sys.stdin.readline().strip('\n')
    data = {'type':18, 'user':USER, 'room':ROOM, 'ans':ans}
    body = json.dumps(data)
    length = len(body)
    send_data = struct.pack('i', length) + body.encode()
    try:
        SOCK_FD.sendall(send_data)
    except:
        print "send message error!"
    return

#############################################################
###打印21点游戏题目
#############################################################
def game21_num(data):
    if ROOM != data['room']:
        return
    num = data['num']
    print "***********************************************"
    print "******21game:"
    for i in num:
        print " %d" % i
    print "***********************************************"
    return

#############################################################
###打印21点游戏的获胜者
#############################################################
def game21_rst(data):
    print "**************************************************************"
    if '' == data['user']:
        print "******There is no winner in %s this round" % data['room']
    elif USER == data['user']:
        print "******you are the winner in %s" % data['room']
    else:
        print "******the winner in %s is %s" % (data['room'], data['user'])
    print "**************************************************************"
    return

#############################################################
###根据接收到从服务器发来报文的type决定处理函数
#############################################################
def decode(data):
    if dict != type(data):
        return
    msg_type = data['type']
    if 8 == msg_type:
        game21_num(data)
    elif 10 == msg_type:
        game21_rst(data)
    elif 12 == msg_type:
        creat_room_rep(data)
    elif 13 == msg_type:
        enter_room_rep(data)
    elif 14 == msg_type:
        exit_room_rep(data)
    elif 15 == msg_type:
        room_chat_rep(data)
    elif 16 == msg_type:
        private_chat_rep(data)
    elif 19 == msg_type:
        list_room_rep(data)
    else:
        print "Message Error!\n"

#############################################################
###根据输入的特殊字符，确定处理函数
#############################################################
def wait_input():
    while True:
        msg = sys.stdin.readline().strip('\n')
        if '$create' == msg:                      #创建房间
            create_room()
        elif '$enter' == msg:                     #加入房间
            enter_room()
        elif '$exit' == msg:                      #退出房间
            exit_room()
        elif '$private' == msg:                   #私聊
            private_chat()
        elif '$list' == msg:                      #获取房间列表或者房间内成员列表
            list_room()
        elif '$game' == msg:                      #输入21点游戏答案
            send_21game_ans()
        else:
            input = msg.decode('utf8')            #默认在大厅或者房间内说话
            if '' != ROOM:
                print "<%s>You: %s" % (ROOM, input)
            else:
                print "<hell>You: %s" % input
            room_chat(input)