#*-* coding:gbk *-*
import struct
from hfsutils import *
from threading import Timer
import thread
import os.path
import sys
from time import sleep
import socket
import select
from tables import *
from hdfdefines import *
from hdfconfig import *
from hdfemail import *
import tables
import datetime
import numpy as np

#define ID_HDFTELE_LOGIN            1      
#define ID_HDFTELE_LOGINANSWER      2      
#define ID_HDFTELE_LOGOUT           3      
#define ID_HDFTELE_CLOSE            4      
#define ID_HDFTELE_COMFIRM          6      
#define ID_HDFTELE_COCDETABLE       6      
#define ID_HDFTELE_REQDATA          7      
#define ID_HDFTELE_MARKETCLOSE      8      
#define ID_HDFTELE_TRADINGHALT      9      
#define ID_HDFTELE_TRANSACTION      1101   
#define ID_HDFTELE_ORDERQUEUE       1102
#define ID_HDFTELE_ORDER            1103
#define ID_HDFTELE_ORDERQUEUE_FAST  1104
#define ID_HDFTELE_MARKETDATA       1012   
#define ID_HDFTELE_INDEXDATA        1113   
#define ID_HDFTELE_MARKETOVERVIEW   1115   
#define ID_HDFTELE_ANNOUNCEMENT     1100   

class hfs_online:
    """ hfs online data management """
    def __init__(self):
        #self.h5file = openFile('../data/db.h5', mode='a', title = 'hfs data db file')
        self.h5file = None
        self.h5filepath=''
        self.gidMap = {}
        self.dte = 0
        self.tot_package_n = 0
        self.recv_package_n = 0
        self.recv_k = 0
        self.reading = True
        self.SH_mdMap = {}
        self.SH_tsMap = {}
        self.SH_indexMap = {}
        self.CF_mdfMap = {}

        self.SH_mdMap_savecnt = 0
        self.SH_tsMap_savecnt = 0
        self.SH_indexMap_savecnt = 0
        self.CF_mdfMap_savecnt = 0
        #self.SH_L2_mdMap = {}
        #self.SH_L2_tsMap = {}
        #self.SH_L2_indexMap = {}
        #self.CF_L2_mdfMap = {}

    def __del__(self):
        if self.h5file:
            self.h5file.close()


    def login_hh_server(self, dte, ip, port, username, passwd, recvMode):
        print "login_hh_server dte:",dte
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((ip, port))
        
        msgHeadLen = struct.calcsize('<HHiii')

        #send login message
        patstr = '<HHiii16s32s8s'
        send_buf = struct.pack(patstr, 0x5340, 1, 0, 0, 0, username, passwd, '')
        s.send(send_buf)

        #recv login message
        recv_buf = self.safe_recv(s, msgHeadLen)
        rv = struct.unpack('<HHiii', recv_buf)
        patstr = '64sii' + '4s'*32 + 'i'*32
        msgLen=struct.calcsize(patstr)
        recv_buf = self.safe_recv(s,msgLen)
        rv = struct.unpack(patstr, recv_buf)
        if rv[1] != 1:
            print >>sys.stderr, 'login error!', rv[0], rv[1]
            content= emailMsg._loginErrorContent.format(self.srcMkt,self.srcType,self.dte,username,ip,port)
            self.logger.error(content)
            sendEmail(self.hdfemailinfo,emailMsg._loginErrorTitle,content,'')
            sys.exit()
        else:
            self.logger.info("User {0} login on server {1} port {2}".format(username,ip,port))

        welinfo    = strstrip(rv[0])
        welans     = rv[1]
        nmkt       = rv[2]
        #marketFlag = rv[3]
        print >>sys.stderr, welinfo, welans, nmkt

        #send codetable request
        patstr = '<HHiii4si'
        send_buf = struct.pack(patstr, 0x5340, 6, 0, 0, 0, srcMkt, dte)
        s.send(send_buf)

        #recv codetable
        recv_buf = self.safe_recv(s, msgHeadLen)
        head = struct.unpack('<HHiii', recv_buf)
        msgLen = head[2]
        body = self.safe_recv(s, msgLen)
        schead = struct.unpack('<iii', body[0:struct.calcsize('<iii')])
        src    = schead[0]
        dte    = schead[1]
        cnt    = schead[2]

        self.on_message(head, body)
        print >>sys.stderr, 'processing dte:%d' % (self.dte)

        #send market data request
        patstr = '<HHiii4si'
        #send_buf = struct.pack(patstr, 0x5340, 7, 0, 0, 0, self.srcMkt, recvMode)#recvMode:1回放所有,0,当前时间
        send_buf = struct.pack(patstr, 0x5340, 7, 0, 0, 0, self.srcMkt, 0)
        s.send(send_buf)

        Timer(5, self.on_exit).start()        

        #recv market data
        while self.reading:
            self.tot_package_n+= 1
            self.recv_package_n+= 1

            recv_buf = self.safe_recv(s, msgHeadLen)
            if len(recv_buf) < msgHeadLen: break
            head = struct.unpack('<HHiii', recv_buf)
            msgLen = head[2]
            msgType = head[1]
            body = self.safe_recv(s, msgLen)
            if len(body) < msgLen: break
            self.on_message(head, body)
        #print "ok"
        s.close()

    def on_message(self, head, body):
        if head[1] == 6:
            self.process_code_table(head, body)
        if head[1] == 1012:
            self.process_market_data(head, body)
        elif head[1] == 1016:
            self.process_market_data_futures(head, body)
        elif head[1] == 1101:
            self.process_transaction(head, body)
        elif head[1] == 1102:
            self.process_order_queue(head, body)
        elif head[1] == 1103:
            self.process_single_order(head, body)
        elif head[1] == 1104:
            self.process_fast_order_queue(head, body)
        elif head[1] == 1113:
            self.process_index(head, body)
        elif head[1] == 8:
            self.process_market_close(head, body)
        elif head[1] == 1115:
            self.process_market_overview(head, body)
        else:
            pass

    def on_bmo(self):
        pass

    def save_SH_L2_index(self):
        pass

    def save_SH_L2_ts(self):
       pass
        
    def save_SH_L2_md(self):
        pass
            
    def save_CF_L2_mdf(self):
        pass

    def save_SH_L1_index(self):
        pass

    def save_SH_L1_ts(self):
        return 0

    def save_SH_L1_md(self):
        pass

    def save_CF_L1_mdf(self):
        pass

    def on_amc(self):
        print >>sys.stderr, "on_amc"

        if self.srcType.upper() == 'L2':
            print >>sys.stderr, "on_amc2"
            self.on_amc2()
        else:
            print >>sys.stderr, "on_amc1"
            self.on_amc1()

    def on_check(self):
        pass
    def on_amc2(self):
        self.SH_mdMap_savecnt = self.save_SH_L2_md()
        print >>sys.stderr, "{0}_{1}_md count:".format(self.srcMkt,self.srcType), self.SH_mdMap_savecnt

        self.SH_tsMap_savecnt = self.save_SH_L2_ts()
        print >>sys.stderr, "{0}_{1}_ts count:".format(self.srcMkt,self.srcType), self.SH_tsMap_savecnt

        self.SH_indexMap_savecnt  = self.save_SH_L2_index()
        print >>sys.stderr, "{0}_{1}_index count:".format(self.srcMkt,self.srcType), self.SH_indexMap_savecnt

        self.CF_mdfMap_savecnt = self.save_CF_L2_mdf()
        print >>sys.stderr, "{0}_{1}_mdf count:".format(self.srcMkt,self.srcType), self.CF_mdfMap_savecnt

    def on_amc1(self):
        self.SH_mdMap_savecnt = self.save_SH_L1_md()
        print >>sys.stderr, "{0}_{1}_md count:".format(self.srcMkt,self.srcType), self.SH_mdMap_savecnt

        self.SH_tsMap_savecnt = self.save_SH_L1_ts()
        print >>sys.stderr, "{0}_{1}_ts count:".format(self.srcMkt,self.srcType), self.SH_tsMap_savecnt

        self.SH_indexMap_savecnt = self.save_SH_L1_index()
        print >>sys.stderr, "{0}_{1}_index count:".format(self.srcMkt,self.srcType), self.SH_indexMap_savecnt

        self.CF_mdfMap_savecnt = self.save_CF_L1_mdf()
        print >>sys.stderr, "{0}_{1}_mdf count:".format(self.srcMkt,self.srcType), self.CF_mdfMap_savecnt

    def run(self,srcMkt, srcType, dte):
        print 'run...'
        self.srcMkt  = srcMkt
        self.srcType = srcType
        self.dte     = dte
        print "self.dte run:",self.dte 

        self.hdfdbpathinfo=gethdfdbpathinfo()
        self.hhserverinfo=gethhserverinfo(self.srcType)
        self.hdfemailinfo=gethdfemailinfo()
        print 'init...'
        logPath = "../log/log{0}_{1}_{2}.log".format(self.srcMkt,self.srcType,self.dte)
        self.logger=getLogHandler("HDF",logPath)
        self.logger.info("start to get {0}_{1}_{2} Market Data".format(self.srcMkt,self.srcType,self.dte))

        h5dbType="{0}_{1}".format(srcMkt.upper(),srcType.upper())

        h5filepath=self.hdfdbpathinfo.get(h5dbType)
        print 'start open file...'
        print 'h5filepath:',h5filepath
        #self.h5file=openFile(h5filepath, mode='a', title = 'hfs data db file') #'../data/db.h5'
        self.h5file=open_file(h5filepath, mode='a', title = 'hfs data db file') #'../data/db.h5'
        print 'open file .... ok'

        hhip = self.hhserverinfo.get('ip')
        hhport = int(self.hhserverinfo.get('port'))
        hhuser = self.hhserverinfo.get('user')
        hhpwd = self.hhserverinfo.get('pwd')

        #print 'hhip:{0} hhport:{1} hhuser:{2} hhpwd:{3}'.format(hhip,hhport,hhuser,hhpwd)

        if not (hhip and hhport and hhuser and hhpwd):
            self.logger.error(emailMsg._configErrorContent)
            sendEmail(self.hdfemailinfo,emailMsg._configErrorTitle,emailMsg._configErrorContent,' ')
            sys.exit(-1)

        self.on_bmo()
        #self.login_hh_server(dte, '172.22.137.36', 20001, "lvjieyong", 'ljy123456', 1)
        self.login_hh_server(dte, hhip,hhport, hhuser, hhpwd, 1)
        self.on_amc()
        self.on_check()

    def process_code_table(self, head, buf):
        patstr = '<iiii' #codetable_head
        hlen = struct.calcsize(patstr)
        rv = struct.unpack(patstr, buf[0:hlen])
        enterdte = self.dte 
        self.dte = rv[1]

        if int(enterdte) != int(self.dte):
            print "enter dte:",enterdte,"TDF dte:",self.dte
            print >>sys.stderr, "enter dte:",enterdte,"TDF dte:",self.dte
            str="enter dte:{0},TDF dte:{1}".format(enterdte,self.dte)
            emailtitle = emailMsg._getDataErrorTitle.format(self.srcMkt,self.srcType,enterdte)
            content=emailMsg._getDataErrorContent.format(self.srcMkt,self.srcType,enterdte,str)
            sendEmail(self.hdfemailinfo,emailtitle,content,' ')
                    
            sys.exit(0)

        N = rv[2]
        patstr = 'ii8s16s'
        dpatstr = '<' + patstr
        dlen = struct.calcsize(patstr)
        for i in range(0, N):
            rv = struct.unpack(patstr, buf[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            gid = rv[0]
            srcType = rv[1]
            symb = rv[2][0:6]
            name = rv[3]
            print >>sys.stderr, gid, symb, name, srcType
            self.gidMap[gid] = (symb, name, srcType)

    def process_single_order(self, head, buf):
        pass

    def process_fast_order_queue(self, head, buf):
        pass

    def process_order_queue(self, head, buf):
        pass

    def process_index(self, head, buf):
        patstr = '<i'
        hlen = struct.calcsize(patstr)
        rv = struct.unpack(patstr, buf[0:hlen])
        N = rv[0]

        patstr = 'iiiiiiqqi'
        
        dlen = struct.calcsize(patstr)
        for i in range(0,N):
            rv = struct.unpack(patstr, buf[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            gid  = rv[0]
            tme  = rv[1]

            if gid not in self.gidMap: return
            tkr = self.gidMap[gid][0]

            v= (rv[1], rv[8], rv[2], rv[3], rv[4], rv[5], rv[6], rv[7],datetime.datetime.now())
            if '000300' in tkr: 
                print v
            self.SH_indexMap.setdefault(tkr, []).append(v)

    def process_transaction(self, head, buf):
        return
        #print 'transaction:'
        patstr = '<ii'
        hlen = struct.calcsize(patstr)
        rv = struct.unpack(patstr, buf[0:hlen])
        gid = rv[0]
        N   = rv[1]

        if gid not in self.gidMap: return
        tkr = self.gidMap[gid][0]

        patstr = 'iiiii'
        dlen = struct.calcsize(patstr)
        for i in range(0,N):
            #print 'transaction:'
            rv = struct.unpack(patstr, buf[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme  = rv[0]
            nidx = rv[1]
            prc  = rv[2]
            qty  = rv[3]
            val  = rv[4]
            v= (rv[0], rv[1], rv[2], rv[3], rv[4])
            self.SH_tsMap.setdefault(tkr, []).append(v)

    def process_market_data(self, head, buf):
        patstr = '<' + 'i'*3 + 'I'*5 + 'I'*10 + 'I'*10 + 'I'*10 + 'I'*10 + 'I' + 'q'*4 + 'I'*2 + 'i'*2 + 'I'*2 + '4s'
        slen = struct.calcsize(patstr)

        N = struct.unpack('<i', buf[0:4])[0]
        for i in range(0, N):
            rv = struct.unpack(patstr, buf[(4+slen*i):(4+slen*(i+1))])
            gid = rv[0]
            tme = rv[1]
            lastPx = rv[7]
            totalTradesTraded = rv[48]
            totalVolumeTraded = rv[49]
            totalValueTraded  = rv[50]

            if gid not in self.gidMap: continue
            tkr = self.gidMap[gid][0]

            v1 = [tme,rv[3], rv[4], rv[5], rv[6], rv[7], rv[48], rv[49], rv[50],datetime.datetime.now()]
            v1.extend(rv[8:48])
            v  = tuple(v1)
            if '600030' in tkr: 
                print v
            self.SH_mdMap.setdefault(tkr,[]).append(v)

    def process_market_data_futures(self, head, buf):
        patstr = '<' + 'i'*3 + 'q' + 'I'*6 + 'q'*3 + 'I'*4 + 'i'*2 + 'I'*20
        slen = struct.calcsize(patstr)

        N = struct.unpack('<i', buf[0:4])[0]
        for i in range(0, N):
            rv = struct.unpack(patstr, buf[(4+slen*i):(4+slen*(i+1))])
            gid               = rv[0]
            tme               = rv[1]
            status            = rv[2]
            preOpenInterest   = rv[3]
            lastPx            = rv[9]
            totalVolumeTraded = rv[10]
            totalValueTraded  = rv[11]
            openInterest      = rv[12]
            closePx           = rv[13]
            settlePx          = rv[14]
            highLimit         = rv[15]
            lowLimit          = rv[16]
            preDelta          = rv[17]
            delta             = rv[18]
            askPx             = rv[19]
            askSz             = rv[24]
            bidPx             = rv[29]
            bidSz             = rv[34]

            if gid not in self.gidMap: continue
            tkr               = self.gidMap[gid][0]

            v1= [rv[1], rv[4], rv[3], rv[5], rv[6], rv[7], rv[8], rv[9], rv[12], rv[14], rv[10], rv[11],datetime.datetime.now()]
            v1.extend(rv[19:39])
            v = tuple(v1)
            
            #if '600030' in tkr: 
            #    print v
            self.CF_mdfMap.setdefault(tkr, []).append(v)

    def on_exit(self):
        if self.recv_package_n == 0:
            print >>sys.stderr, 'exit: recv_k:', self.recv_k, 'recv_package_n:', self.recv_package_n
            self.reading = False
            #emailtitle = emailMsg._systemOnExitErrorTitle.format(self.srcMkt,self.srcType,self.dte)
            #content=emailMsg._systemOnExitErrorContent.format(self.srcMkt,self.srcType,self.dte,5)
            #sendEmail(self.hdfemailinfo,emailtitle,content,' ')
            return
        else:
            self.recv_package_n = 0
        
        self.recv_k+= 1
        print  >>sys.stderr, "%s\r" % ("."*(self.tot_package_n/100000+1) + " tot:" + str(self.tot_package_n) \
                                           + " k:" + str(self.recv_k)),
        Timer(5, self.on_exit).start()

    def safe_recv(self, s, nlen,timeout=5):
        ''' 网络通信时，接收指定长度的字节流 '''
        n = 0
        to_recv = nlen
        rv = ''
        while self.reading:
            buf = ''
            try:
                recvtimeout=select.select([s],[],[],timeout)
                if recvtimeout[0] == []:
                    #print >>sys.stderr, "recv hh response timeout,set timeout time is :%s " % (timeout)
                    #send email and the exit
                    emailtitle = emailMsg._timeoutErrorTitle.format(self.srcMkt,self.srcType,self.dte)
                    content=emailMsg._timeoutErrorContent.format(self.srcMkt,self.srcType,self.dte,timeout)
                    sendEmail(self.hdfemailinfo,emailtitle,content,' ')
                    #self.logger.error("recvtimeout:{0}s,SystemExit.".format(timeout))
                    timeounterror="recv hh response timeout,{0},set timeout time is :{1}s ,headcontent:{2}".format(emailtitle,timeout,self.headcontent)
                    self.logger.error(timeounterror)
                    #print "rec try"
                    #sys.exit(-1)
                buf = s.recv(to_recv)
            except Exception,ex:
                #print "rec rec_excep"
                self.logger.error("safe_recv,nlen:{0},Error:{1}".format(nlen,ex))
                #sys.exit(-1)
                #pass
            rv+= buf
            to_recv-= len(buf)
            if to_recv == 0: break
        return rv
    
    def process_market_close(self,head,buf):
        self.reading = False  #market close ,set recvFlag=false

    def process_market_overview(self,head,buf):
        self.reading = False #market over view ,set recvFlag=false

    def check_market_data(self,checkfilepathinfo):
        return

    def check_transaction(self,checkfilepathinfo):
        return

    def check_index(self,checkfilepathinfo):
        return

    def check_market_data_futures(self,checkfilepathinfo):
        return 


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print >>sys.stderr, "usage:%s SH/SZ/CF L2/L1 dte,give 4 param." % (sys.argv[0])
        hdfemailinfo = gethdfemailinfo()
        send = sendEmail(hdfemailinfo,emailMsg._paramErrorTitle,emailMsg._paramErrorContent,'')
        sys.exit(-1)

    srcMkt  = sys.argv[1]
    srcType = sys.argv[2]
    dte     = int(sys.argv[3])

    if srcMkt not in set(['SZ', 'SH', 'CF']):
        print >>sys.stderr, "usage:%s SH/SZ/CF L2/L1 dte" % (sys.argv[0])
        hdfemailinfo = gethdfemailinfo()
        send = sendEmail(hdfemailinfo,emailMsg._paramErrorTitle,emailMsg._paramErrorContent,'')
        sys.exit(-1)

    #mod by oliver 2013-08-29
    #hfs_online().run(srcType, dte)
    hfs_online().run(srcMkt,srcType, dte)
    #end mod by jwh 201308-29

