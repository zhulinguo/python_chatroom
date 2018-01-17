# -*- coding:utf-8 -*-
import json
import time
import datetime
import struct
import random
import re

#############################################################
###本文件负责所有数据处理
#############################################################
USER_FILE = None            #保存账号的文件指针
USER_INFO = {}              #已经登陆的账号的临时信息 {用户名:{'room':所在房间, 'fd':连接句柄, 'game':是否已经参与游戏}}
ROOM_INFO = {}              #已经创建的房间的临时信息 {房间名:{'cnt':成员个数, 'member':{所有成员名字}, 'game':{'winner':获胜者, 'ans':目前为止最佳结果, 'num':题目的4个数字}}}
GAME_START = False          #21点游戏开始和关闭的标记
INPUTS = []                 #select所监听的socket队列

#############################################################
###初始化打开账户信息文件，文件保存了"账号"，"密码"，"在线时长"
#############################################################
def init():
    global USER_FILE
    USER_FILE = open('user.txt', 'r+')
    return

#################################################################
###账号断连时，将对应的账号信息从内存清空，将本次在线时长添加进总时长里保存
#################################################################
def clear_sock(fd):
    global USER_INFO
    global USER_FILE
    global INPUTS
    user = ''
    room = ''
    INPUTS.remove(fd)
    try:
        fd.close()
    except:
        pass
    for temp in USER_INFO:
        if fd == USER_INFO[temp]['fd']:
            room = USER_INFO[temp]['room']
            user = temp
            break
    if '' == user:
        return
    else:
        online_time = time.time() - USER_INFO[user]['login_time']       #下线时间减去上线时间
        USER_FILE.seek(0, 0)
        lines = USER_FILE.readlines()
        USER_FILE.truncate()
        USER_FILE.seek(0, 0)
        for line in lines:
            if '' == line:
                continue
            try:
                info = json.loads(line)
            except:
                continue
            if info['user'] == user:
                info['time'] = info['time'] + online_time
                line = json.dumps(info)+'\n'
            USER_FILE.write(line)
        USER_FILE.flush()
        USER_INFO.pop(user)
        if '' != room:
            ROOM_INFO[room]['member'].remove(user)
            ROOM_INFO[room]['cnt'] = ROOM_INFO[room]['cnt'] - 1
            if 0 == ROOM_INFO[room]['cnt']:
                del ROOM_INFO[room]
    return

###########################################################################
###发送报文的接口，传入"要发送的内容"，"要发送的目的的fd组成的集合"以及"需要排除的fd"
###########################################################################
def send_message(message, send_fd_set, src_fd):
    length = len(message)
    message = struct.pack('i', length) + message.encode()
    for target in send_fd_set:
        if target != src_fd:
            try:
                target.sendall(message)
            except:
                clear_sock(target)

#################################################################
###生成4个1-10的数字放进list返回
#################################################################
def generate_21():
    num = []
    for i in range(0, 4):
        num.append(random.randint(1, 10))
    num.sort()
    return num

#################################################################
###发送21点游戏的最终获胜者给房间所有人，如果没有人获胜，则不发送
#################################################################
def send_21game_rst():
    for room in ROOM_INFO:
        message = {'type':10, 'room':room, 'user':ROOM_INFO[room]['game']['winner']}
        send_fd_set = {USER_INFO[member]['fd'] for member in ROOM_INFO[room]['member']}
        ROOM_INFO[room]['game']['winner'] = ''
        ROOM_INFO[room]['game']['ans'] = 0
        message = json.dumps(message)
        send_message(message, send_fd_set, 0)
    return

#################################################################
###发布21点游戏的题目，每个房间的题目不一样
#################################################################
def send_21game():
    for room in ROOM_INFO:
        num = generate_21()
        ROOM_INFO[room]['game'] = {'num':num, 'winner':'', 'ans':0}
        message = {'type':8, 'room':room, 'num':num}
        send_fd_set = {USER_INFO[member]['fd'] for member in ROOM_INFO[room]['member']}
        message = json.dumps(message)
        send_message(message, send_fd_set, 0)
    return

#################################################################
###计算发来的21点游戏答案
#################################################################
def check_ans(ans, num):
    ans_num = re.findall('(\w*[0-9]+)\w*', ans)
    ans_num = [int(i) for i in ans_num]
    ans_num.sort()
    if ans_num != num:
        return -1
    else:
        try:
            ans = eval(ans)
        except:
            return -1
    return ans

#################################################################
###处理发来的21点游戏答案，根据答案更新房间中保存的本次游戏获胜者信息
#################################################################
def game_rsp(data):
    user = data['user']
    if USER_INFO[user]['game']:                              #如果这个用户已经提交过答案了，则直接返回
        return
    else:
        USER_INFO[user]['game'] = True
    ans = data['ans']
    room = data['room']
    if 21 == ROOM_INFO[room]['game']['ans']:
        return
    num = ROOM_INFO[room]['game']['num']
    ans = check_ans(ans, num)
    if ans <= ROOM_INFO[room]['game']['ans'] or ans > 21:    #如果答案大于21或者没有比之前其它所有人的答案靠近21则直接返回
        return
    else:
        ROOM_INFO[room]['game']['ans'] = ans
        ROOM_INFO[room]['game']['winner'] = user
    return

###################################################################
###21点游戏的定时器，第一次触发在下一个准点或者准点半，之后每过半小时触发一次
###################################################################
def game_timer():
    global GAME_START
    now = datetime.datetime.now()
    if now.minute >= 30:
        if 23 == now.hour:
            oneday = datetime.timedelta(days=1)
            today = datetime.date.today()
            tomorror = today + oneday
            target_time = datetime.datetime(tomorror.year, tomorror.month, tomorror.day, 0, 0, 0)
            end_time = datetime.datetime(tomorror.year, tomorror.month, tomorror.day, 0, 0, 15)
        else:
            target_time = datetime.datetime(now.year, now.month, now.day, now.hour+1, 0, 0)
            end_time = datetime.datetime(now.year, now.month, now.day, now.hour + 1, 0, 15)
    else:
        target_time = datetime.datetime(now.year, now.month, now.day, now.hour, 30, 0)
        end_time = datetime.datetime(now.year, now.month, now.day, now.hour, 30, 15)
    while True:
        now = datetime.datetime.now()
        if now > target_time:
            GAME_START = True
            target_time = target_time + datetime.timedelta(minutes=30)
            send_21game()
        elif now > end_time:
            GAME_START = False
            for user in USER_INFO:
                USER_INFO[user]['game'] = False
            end_time = target_time + datetime.timedelta(seconds=15)
            send_21game_rst()


#################################################################
###处理发来的注册报文
###在文件中如果找到对应账号，则返回报文errorcode:1,成功返回errorcode:0
#################################################################
def register(data, src_fd):
    global USER_FILE
    USER_FILE.seek(0, 0)
    pos = 0
    while True:
        try:
            pos = USER_FILE.tell()
            info = USER_FILE.readline()
            info = json.loads(info)
        except:
            break
        if info['user'] == data['user']:
            response = {'type':11, 'user':data['user'], 'errorcode':1}
            response = json.dumps(response)
            send_message(response, {src_fd}, 0)
            return
    USER_FILE.seek(pos, 0)
    temp = {'user':data['user'], 'password':data['password'], 'time':0}
    temp = json.dumps(temp)
    USER_FILE.write(temp + '\n')
    USER_FILE.flush()
    response = {'type':11, 'user':data['user'], 'errorcode':0}
    response = json.dumps(response)
    send_message(response, {src_fd}, 0)
    return

###################################################################
###创建新的房间
###如果房间已存在，返回报文errorcode:1，成功返回errorcode:0
###################################################################
def create_room(data, src_fd):
    global ROOM_INFO
    global USER_INFO
    room = data['room']
    user = data['user']
    if room in ROOM_INFO.keys():
        response = {'type':12, 'room':data['room'], 'errorcode':1}
        response = json.dumps(response)
        send_message(response, {src_fd}, 0)
        return
    ROOM_INFO[room] = {'password':data['password'], 'cnt':1, 'member':{user}, 'game':{'ans':0, 'winner':''}}
    USER_INFO[user]['room'] = room
    response = {'type':12, 'room':data['room'], 'errorcode':0}
    response = json.dumps(response)
    send_message(response, {src_fd}, 0)
    return

###################################################################
###加入房间
###如果房间不存在，返回报文errorcode:1，如果密码错误返回errorcode:2
###成功返回errorcode:0
###################################################################
def enter_room(data, src_fd):
    global USER_INFO
    global ROOM_INFO
    room = data['room']
    user = data['user']
    if room not in ROOM_INFO.keys():
        response = {'type':13, 'room':data['room'], 'errorcode':1}
        response = json.dumps(response)
        send_message(response, {src_fd}, 0)
        return
    if ROOM_INFO[room]['password'] != data['password']:
        response = {'type':13, 'room':data['room'], 'errorcode':2}
        response = json.dumps(response)
        send_message(response, {src_fd}, 0)
        return
    ROOM_INFO[room]['member'].add(user)
    ROOM_INFO[room]['cnt'] = ROOM_INFO[room]['cnt'] + 1
    USER_INFO[user]['room'] = data['room']
    response = {'type':13, 'room':data['room'], 'errorcode':0}
    response = json.dumps(response)
    send_message(response, {src_fd}, 0)
    return

###################################################################
###退出房间，如果退出后，房间人数为0则删除该房间
###成功返回errorcode:0
###################################################################
def exit_room(data, src_fd):
    global ROOM_INFO
    global USER_INFO
    room = data['room']
    if '' == room:
        return
    user = data['user']
    USER_INFO[user]['room'] = ''
    ROOM_INFO[room]['member'].remove(user)
    ROOM_INFO[room]['cnt'] = ROOM_INFO[room]['cnt'] - 1
    if 0 == ROOM_INFO[room]['cnt']:
        del ROOM_INFO[room]
    response = {'type':14, 'room':data['room'], 'errorcode':0}
    response = json.dumps(response)
    send_message(response, {src_fd}, 0)
    return

###################################################################
###修改报文类型后，转发报文内容给房间中所有其它成员
###################################################################
def room_chat(data, src_fd):
    global USER_INFO
    global ROOM_INFO
    room = data['room']
    data['type'] = 15
    if '' == room:
        send_fd_set = {USER_INFO[member]['fd'] for member in USER_INFO.keys() if USER_INFO[member]['room'] == ''}
    else:
        send_fd_set = {USER_INFO[member]['fd'] for member in ROOM_INFO[room]['member']}
    message = json.dumps(data)
    send_message(message, send_fd_set, src_fd)
    return

###################################################################
###修改报文类型后，转发报文给对应账户的连接
###################################################################
def private_chat(data, src_fd):
    global USER_INFO
    target = data['target']
    if target not in USER_INFO.keys():
        send_fd_set = {src_fd}
    else:
        send_fd_set = {USER_INFO[target]['fd']}
    data['type'] = 16
    message = json.dumps(data)
    send_message(message, send_fd_set, 0)
    return

###################################################################
###如果请求方已经在房间内，则返回房间内的成员列表
###如果请求方不在房间里面，则返回所有聊天室的列表
###################################################################
def list_room(data, src_fd):
    global USER_INFO
    global ROOM_INFO
    room = data['room']
    if '' == room:
        member_list = [member for member in ROOM_INFO.keys()]
    else:
        member_list = [member for member in ROOM_INFO[room]['member']]
    message = {'type':19, 'room':room, 'list':member_list}
    message = json.dumps(message)
    send_message(message, {src_fd}, 0)
    return

###################################################################
###处理登陆报文，登陆成功后自动处于大厅
###如果账户已在线，则将之前登陆的连接踢下线
###如果账户不存在，则将返回报文errorcode:1
###如果密码错误，则返回报文errorcode:2
###成功返回errorcode:0
###################################################################
def login(data, src_fd):
    global USER_FILE
    global USER_INFO
    global INPUTS
    user = data['user']
    password = data['password']
    USER_FILE.seek(0, 0)
    lines = USER_FILE.readlines()
    for info in lines:
        try:
            info = json.loads(info)
        except:
            break
        if info['user'] == user:
            if info['password'] != password:
                response = {'type':17, 'user':data['user'], 'errorcode':2}
                message = json.dumps(response)
                send_message(message, {src_fd}, 0)
                return
            if user in USER_INFO.keys():
                pre_fd = USER_INFO[user]['fd']
                INPUTS.remove(pre_fd)
                pre_fd.close()
                USER_INFO[user]['fd'] = src_fd
            else:
                USER_INFO[user] = {'fd':src_fd, 'room':'', 'login_time':time.time(), 'game':False}
            response = {'type': 17, 'user': data['user'], 'errorcode': 0}
            message = json.dumps(response)
            send_message(message, {src_fd}, 0)
            return
    response = {'type': 17, 'user': data['user'], 'errorcode': 1}
    message = json.dumps(response)
    send_message(message, {src_fd}, 0)
    return

###################################################################
###接收到客户端请求报文，根据数据中的type选择不同的处理
###################################################################
def decode(data, src_fd):
    global GAME_START
    if dict != type(data):
        return
    msg_type = data['type']
    if 1 == msg_type:    #注册报文
        register(data, src_fd)
    elif 2 == msg_type:
        create_room(data, src_fd)
    elif 3 == msg_type:
        enter_room(data, src_fd)
    elif 4 == msg_type:
        exit_room(data, src_fd)
    elif 5 == msg_type:
        room_chat(data, src_fd)
    elif 6 == msg_type:
        private_chat(data, src_fd)
    elif 7 == msg_type:
        login(data, src_fd)
    elif 9 == msg_type:
        list_room(data, src_fd)
    elif 18 == msg_type:
        if GAME_START:
            game_rsp(data)
    else:
        print "Message Error!\n"