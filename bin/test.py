# -*- coding: gbk -*- #
import sys, os, datetime
import struct
import socket
import select
import errno
import redis
from threading import Timer, Thread
from multiprocessing import Process
from hfsutils import *
from hdfconfig import *
from hdfparser import hfs_hh_parser
from hdfdumper import hfs_hh_dumper


class hfs_writer:
    """ hfs data management (online & offline) """
    def __init__(self, dte, srcMkt, srcType, recvMode):
        self.dte = dte
        self.srcMkt = srcMkt
        self.srcType = srcType
        self.recvMode = recvMode

        self.reading = True
        self.process = []

        # self.recv_package_n = 0
        # self.recv_k_n = 0
        # self.recv_package_size = 0
        # self.recv_k_size = 0
        # self.snapshot = ""
        
        self.r = redis.Redis('192.168.1.16')
        self.redis_tkr_raw_key = 'TKRS_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType
        self.redis_db_raw_key = 'DB_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType
        self.redis_stream_raw_key = 'STREAM_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType


    def login_hh_server(self, ip, port, username, passwd):
        print "login_hh_server dte: ", self.dte
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((ip, port))

        msgHeadLen = struct.calcsize('<HHiii')

        # 发送登录请求
        patstr = '<HHiii16s32s8s'
        send_buf = struct.pack(patstr, 0x5340, 1, 0, 0, 0, username, passwd, '')
        s.send(send_buf)

        # 接收登录信息
        recv_buf = self.safe_recv(s, msgHeadLen)
        rv = struct.unpack('<HHiii', recv_buf)
        patstr = '64sii' + '4s'*32 + 'i'*32
        msgLen=struct.calcsize(patstr)
        recv_buf = self.safe_recv(s,msgLen)
        rv = struct.unpack(patstr, recv_buf)
        if rv[1] != 1:
            print >>sys.stderr, 'login error!', rv[0], rv[1]
            sys.exit(-1)
        else:
            print("User {0} login on server {1} port {2}".format(username,ip,port))

        # 发送合约请求
        patstr = '<HHiii4si'
        send_buf = struct.pack(patstr, 0x5340, 6, 0, 0, 0, srcMkt, self.dte)
        s.send(send_buf)

        # 接收合约列表
        recv_buf = self.safe_recv(s, msgHeadLen)
        head = struct.unpack('<HHiii', recv_buf)
        msgLen = head[2]
        body = self.safe_recv(s, msgLen)
        schead = struct.unpack('<iii', body[0:struct.calcsize('<iii')])
        src    = schead[0]
        dte    = schead[1]
        cnt    = schead[2]

        # 将合约列表写入redis
        self.r.set(self.redis_tkr_raw_key, body) # TODO
        
        # 启动解析进程
        if self.recvMode == 0: # online模式下同时启动redis解析
            print "online mode, start tick parser..."
            p = Process(target = hfs_hh_parser(self.dte, self.srcMkt, self.srcType).run, name = 'hdfparser')
            p.start()
            self.process.append(p)

        # 启动归档进程
        print "start tick dumper..."
        p = Process(target = hfs_hh_dumper(self.dte, self.srcMkt, self.srcType).run, name = 'hdfdumper')
        p.start()
        self.process.append(p)

        # 测速
        # Timer(10, self.on_timer).start()

        # 发送市场行情请求
        patstr = '<HHiii4si'
        send_buf = struct.pack(patstr, 0x5340, 7, 0, 0, 0, self.srcMkt, self.recvMode)
        s.send(send_buf)

        # 接收市场行情数据
        while self.reading:
            recv_buf = self.safe_recv(s, msgHeadLen)
            if len(recv_buf) < msgHeadLen: break
            head = struct.unpack('<HHiii', recv_buf)
            msgLen = head[2]
            msgType = head[1]
            body = self.safe_recv(s, msgLen)
            if len(body) < msgLen: break
            # self.recv_package_n += 1
            # self.recv_package_size += len(body)
            if head[1] == 1012 or head[1] == 1113:
                self.r.publish(self.redis_stream_raw_key, (head, body)) # TODO 数据量太大暂时只publish
                # self.recv_k_n += 1
                # self.recv_k_size += len(body)
                # self.snapshot = body
                # self.r.rpush(self.redis_db_raw_key, (head, body))
            if head[1] == 8 or head[1] == 1115: 
                self.r.publish(self.redis_stream_raw_key, (head, body)) # 发布市场结束消息给下游
                print >>sys.stderr, 'market close, exit.'
                self.reading = False

        s.close() # 关闭socket连接

        # 等待后台进程完成
        for p in self.process:
            p.join()

    def on_timer(self):
        # 查看tick时间
        buf = self.snapshot
        if len(buf) == 260:
            patstr = '<' + 'i'*3 + 'I'*5 + 'I'*10 + 'I'*10 + 'I'*10 + 'I'*10 + 'I' + 'q'*4 + 'I'*2 + 'i'*2 + 'I'*2 + '4s'
        else:
            patstr = 'i'*6 + 'q'*2 + 'i'
        slen = struct.calcsize(patstr)
        N = struct.unpack('<i', buf[0:4])[0]
        for i in range(N):
            rv = struct.unpack(patstr, buf[4:(4 + slen)])
            gid, tme, status, pclse, opn, high, low, lastPx = rv[:8]
            now = datetime.datetime.now()
            tme = str(float(tme) / 1e3)
            tme = str(tme.split('.')[0]).zfill(6) + '.' + tme.split('.')[1]
            tme = datetime.datetime.strptime(str(self.dte) + tme, '%Y%m%d%H%M%S.%f')
            print "current time: ", now
            print "current tick time: ", tme
            print "delayed seconds: {}s".format((now - tme).total_seconds())
        
        # 报告流量
        print "count: total - {} packages/s; market data - {} packages/s".format(self.recv_package_n / 10, self.recv_k_n / 10)
        print "speed: total - {} KB/s; market data - {} KB/s".format(self.recv_package_size / 1e3, self.recv_k_size / 1e3)
        self.recv_package_n = 0
        self.recv_k_n = 0
        self.recv_package_size = 0
        self.recv_k_size = 0

        Timer(10, self.on_timer).start()

    def run(self):
        # 读取配置文件
        self.hhserverinfo = gethhserverinfo(self.srcType)
        hhip = self.hhserverinfo.get('ip')
        hhport = int(self.hhserverinfo.get('port'))
        hhuser = self.hhserverinfo.get('user')
        hhpwd = self.hhserverinfo.get('pwd')

        # 登陆并订阅数据
        self.login_hh_server(hhip,hhport, hhuser, hhpwd) # 0: 实时

    def safe_recv(self, s, nlen, timeout=5):
        """ 网络通信时，接收指定长度的字节流 """
        n = 0
        to_recv = nlen
        rv = ''
        while self.reading:
            buf = ''
            try:
                recvtimeout = select.select([s], [], [], timeout)
                if recvtimeout[0] == []:
                    now = datetime.datetime.now()
                    print >>sys.stderr, "{0}: recv hh response timeout, set timeout time is: {1}".format(now, timeout)
                buf = s.recv(to_recv)
            except socket.error, e:
                now = datetime.datetime.now()
                if e.errno == errno.ECONNRESET:
                    print >>sys.stderr, '{0}: socket disconnect, exit.'.format(now)
                    for p in self.process: p.terminate()
                    sys.exit(-1)
                else:
                    print >>sys.stderr, "{0}: socket error: {1}".format(now, e)
            except Exception, e:
                now = datetime.datetime.now()
                print >>sys.stderr, "{0}: safe_recv, nlen: {1}, Error: {2}".format(now, nlen, e)
            rv += buf
            to_recv -= len(buf)
            if to_recv == 0: break

        return rv


if __name__ == '__main__':

    if len(sys.argv) < 4:
        print >>sys.stderr, "usage:%s SH/SZ/CF L2/L1 dte [recvMode], at least 4 param." % (sys.argv[0])
        sys.exit(-1)

    srcMkt  = sys.argv[1]
    srcType = sys.argv[2]
    dte     = int(sys.argv[3])
    recvMode = int(sys.argv[4]) if len(sys.argv) > 4 else 0 # 默认只接受实时行情

    tradedays = [int(x[0]) for x in [line.strip().split() for line in open('../config/calendar.txt')] if len(x) == 6]

    if dte not in tradedays:
        print >>sys.stderr, 'not tradeday, exit.'
        sys.exit(0)

    if srcMkt not in set(['SZ', 'SH', 'CF']):
        print >>sys.stderr, "usage:%s SH/SZ/CF L2/L1 dte [recvMode]" % (sys.argv[0])
        sys.exit(-1)

    hfs_writer(dte, srcMkt, srcType, recvMode).run()

