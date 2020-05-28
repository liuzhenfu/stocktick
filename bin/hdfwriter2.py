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
    def __init__(self, dte, srcMkt, srcType):
        self.dte = dte
        self.srcMkt = srcMkt
        self.srcType = srcType
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
        send_buf = struct.pack(patstr, 0x5340, 7, 0, 0, 0, self.srcMkt, recvMode)
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
        gname = '/%s_%s_index/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt = 0
        for tkr in self.SH_indexMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.removeNode(gname, name)
                print 'remove index', gname, name

            table = self.h5file.create_table(gname, name, market_index, 'index data', \
                                            expectedrows=10000, createparents=True)
            mindex    = table.row
            for x in self.SH_indexMap[tkr]:
                (tme,pclse,opn,high,low,lastPx,volume,value) = x

                mindex['dte'] = self.dte
                mindex['tme'] = tme
                mindex['pclse'] = pclse
                mindex['opn'] = opn
                mindex['high'] = high
                mindex['low'] = low
                mindex['lastPx'] = lastPx
                mindex['volume'] = volume
                mindex['value']  = value
                mindex.append()
                cnt = cnt + 1
            table.flush()
        return cnt

    def save_SH_L2_ts(self):
        gname = '/%s_%s_transaction/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt = 0
        for tkr in self.SH_tsMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.removeNode(gname, name)
                print 'remove ts', gname, name

            table = self.h5file.create_table(gname, name, transaction, 'transaction data', \
                                            expectedrows=10000, createparents=True)
            ts    = table.row
            for x in self.SH_tsMap[tkr]:
                (tme,nidx,prc,qty,val) = x
                ts['dte'] = self.dte
                ts['tme'] = tme
                ts['idx'] = nidx
                ts['prc'] = prc
                ts['qty'] = qty
                ts['val'] = val
                ts.append()
                cnt = cnt + 1
            table.flush()
        return cnt

    def save_SH_L2_md(self):
        gname = '/%s_%s_market_data/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt = 0
        for tkr in self.SH_mdMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.removeNode(gname, name)
                print 'remove md', gname, name

            table = self.h5file.create_table(gname, 't%s'%(tkr), market_data, 'market data', \
                                            expectedrows=4500, createparents=True)
            md    = table.row
            for x in self.SH_mdMap[tkr]:
                (tme,pclse,opn,high,low,lastPx,tcount,volume,value,\
                 ask1,ask2,ask3,ask4,ask5,ask6,ask7,ask8,ask9,ask10,\
                 asize1,asize2,asize3,asize4,asize5,asize6,asize7,asize8,asize9,asize10,\
                 bid1,bid2,bid3,bid4,bid5,bid6,bid7,bid8,bid9,bid10,\
                 bsize1,bsize2,bsize3,bsize4,bsize5,bsize6,bsize7,bsize8,bsize9,bsize10) = x

                md['dte']   = self.dte
                md['tme']   = tme
                md['pclse'] = pclse
                md['opn']   = opn
                md['high']  = high
                md['low']   = low
                md['lastPx']= lastPx

                md['ask1']  = ask1
                md['ask2']  = ask2
                md['ask3']  = ask3
                md['ask4']  = ask4
                md['ask5']  = ask5
                md['ask6']  = ask6
                md['ask7']  = ask7
                md['ask8']  = ask8
                md['ask9']  = ask9
                md['ask10'] = ask10

                md['asize1']  = asize1
                md['asize2']  = asize2
                md['asize3']  = asize3
                md['asize4']  = asize4
                md['asize5']  = asize5
                md['asize6']  = asize6
                md['asize7']  = asize7
                md['asize8']  = asize8
                md['asize9']  = asize9
                md['asize10'] = asize10

                md['bid1']  = bid1
                md['bid2']  = bid2
                md['bid3']  = bid3
                md['bid4']  = bid4
                md['bid5']  = bid5
                md['bid6']  = bid6
                md['bid7']  = bid7
                md['bid8']  = bid8
                md['bid9']  = bid9
                md['bid10'] = bid10

                md['bsize1']  = bsize1
                md['bsize2']  = bsize2
                md['bsize3']  = bsize3
                md['bsize4']  = bsize4
                md['bsize5']  = bsize5
                md['bsize6']  = bsize6
                md['bsize7']  = bsize7
                md['bsize8']  = bsize8
                md['bsize9']  = bsize9
                md['bsize10'] = bsize10

                md['tcount']  = tcount
                md['volume']  = volume
                md['value']   = value

                md.append()
                cnt = cnt + 1
            table.flush()
        return cnt

    def save_CF_L2_mdf(self):
        gname = '/%s_%s_market_data_futures/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt   = 0
        for tkr in self.CF_mdfMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.removeNode(gname, name)
                print 'remove md', gname, name

            table = self.h5file.create_table(gname, 't%s'%(tkr), market_data_futures, 'market data futures', \
                                            expectedrows=4500, createparents=True)
            mdf    = table.row
            for x in self.CF_mdfMap[tkr]:
                (tme,pclse, popi, psettle,opn,high,low,lastPx,opi,settle,volume,value,\
                 ask1,ask2,ask3,ask4,ask5,\
                 asize1,asize2,asize3,asize4,asize5,\
                 bid1,bid2,bid3,bid4,bid5,\
                 bsize1,bsize2,bsize3,bsize4,bsize5) = x

                mdf['dte']   = self.dte
                mdf['tme']   = tme
                mdf['pclse'] = pclse
                mdf['popi']  = popi
                mdf['psettle'] = psettle
                mdf['opn']   = opn
                mdf['high']  = high
                mdf['low']   = low
                mdf['lastPx']= lastPx
                mdf['opi']   = opi
                mdf['settle'] = settle
                mdf['volume']  = volume
                mdf['value']   = value

                mdf['ask1']  = ask1
                mdf['ask2']  = ask2
                mdf['ask3']  = ask3
                mdf['ask4']  = ask4
                mdf['ask5']  = ask5

                mdf['asize1']  = asize1
                mdf['asize2']  = asize2
                mdf['asize3']  = asize3
                mdf['asize4']  = asize4
                mdf['asize5']  = asize5

                mdf['bid1']  = bid1
                mdf['bid2']  = bid2
                mdf['bid3']  = bid3
                mdf['bid4']  = bid4
                mdf['bid5']  = bid5

                mdf['bsize1']  = bsize1
                mdf['bsize2']  = bsize2
                mdf['bsize3']  = bsize3
                mdf['bsize4']  = bsize4
                mdf['bsize5']  = bsize5

                mdf.append()
                cnt = cnt + 1
            table.flush()
        return cnt

    def save_SH_L1_index(self):
        gname = '/%s_%s_index/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt = 0
        for tkr in self.SH_indexMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.removeNode(gname, name)
                print 'remove index', gname, name

            table = self.h5file.create_table(gname, name, market_index, 'index data', \
                                            expectedrows=10000, createparents=True)
            mindex    = table.row
            for x in self.SH_indexMap[tkr]:
                (tme,pclse,opn,high,low,lastPx,volume,value) = x

                mindex['dte'] = self.dte
                mindex['tme'] = tme
                mindex['pclse'] = pclse
                mindex['opn'] = opn
                mindex['high'] = high
                mindex['low'] = low
                mindex['lastPx'] = lastPx
                mindex['volume'] = volume
                mindex['value'] = value
                mindex.append()
                cnt = cnt + 1
            table.flush()
        return cnt

    def save_SH_L1_ts(self):
        return 0

    def save_SH_L1_md(self):
        gname = '/%s_%s_market_data/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt = 0
        for tkr in self.SH_mdMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.removeNode(gname, name)
                print 'remove md', gname, name

            table = self.h5file.create_table(gname, 't%s'%(tkr), market_data_L1, 'market data', \
                                            expectedrows=4500, createparents=True)
            md    = table.row
            for x in self.SH_mdMap[tkr]:
                (tme,pclse,opn,high,low,lastPx,tcount,volume,value,\
                 ask1,ask2,ask3,ask4,ask5,ask6,ask7,ask8,ask9,ask10,\
                 asize1,asize2,asize3,asize4,asize5,asize6,asize7,asize8,asize9,asize10,\
                 bid1,bid2,bid3,bid4,bid5,bid6,bid7,bid8,bid9,bid10,\
                 bsize1,bsize2,bsize3,bsize4,bsize5,bsize6,bsize7,bsize8,bsize9,bsize10) = x

                md['dte']   = self.dte
                md['tme']   = tme
                md['pclse'] = pclse
                md['opn']   = opn
                md['high']  = high
                md['low']   = low
                md['lastPx']= lastPx

                md['ask1']  = ask1
                md['ask2']  = ask2
                md['ask3']  = ask3
                md['ask4']  = ask4
                md['ask5']  = ask5

                md['asize1']  = asize1
                md['asize2']  = asize2
                md['asize3']  = asize3
                md['asize4']  = asize4
                md['asize5']  = asize5

                md['bid1']  = bid1
                md['bid2']  = bid2
                md['bid3']  = bid3
                md['bid4']  = bid4
                md['bid5']  = bid5

                md['bsize1']  = bsize1
                md['bsize2']  = bsize2
                md['bsize3']  = bsize3
                md['bsize4']  = bsize4
                md['bsize5']  = bsize5

                md['volume']  = volume
                md['value']   = value

                md.append()
                cnt = cnt + 1
            table.flush()
        return cnt

    def save_CF_L1_mdf(self):
        gname = '/%s_%s_market_data_futures/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt   = 0
        for tkr in self.CF_mdfMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.removeNode(gname, name)
                print 'remove md', gname, name

            table = self.h5file.create_table(gname, 't%s'%(tkr), market_data_futures_L1, 'market data futures', \
                                            expectedrows=4500, createparents=True)
            mdf    = table.row
            for x in self.CF_mdfMap[tkr]:
                (tme,pclse, popi, psettle,opn,high,low,lastPx,opi,settle,volume,value,\
                 ask1,ask2,ask3,ask4,ask5,\
                 asize1,asize2,asize3,asize4,asize5,\
                 bid1,bid2,bid3,bid4,bid5,\
                 bsize1,bsize2,bsize3,bsize4,bsize5) = x

                mdf['dte']   = self.dte
                mdf['tme']   = tme
                mdf['pclse'] = pclse
                mdf['popi']  = popi
                mdf['psettle'] = psettle
                mdf['opn']   = opn
                mdf['high']  = high
                mdf['low']   = low
                mdf['lastPx']= lastPx
                mdf['opi']   = opi
                mdf['settle'] = settle
                mdf['volume']  = volume
                mdf['value']   = value
                mdf['ask1']  = ask1
                mdf['asize1']  = asize1
                mdf['bid1']  = bid1
                mdf['bsize1']  = bsize1
                mdf.append()
                cnt = cnt + 1
            table.flush()
        return cnt

    def on_amc(self):
        print >>sys.stderr, "on_amc"

        if self.srcType.upper() == 'L2':
            print >>sys.stderr, "on_amc2"
            self.on_amc2()
        else:
            print >>sys.stderr, "on_amc1"
            self.on_amc1()

    def on_check(self):
        print >>sys.stderr, "on_check"
        checkfilepathinfo=getcheckfilepathinfo()
        errflag=False
        htmlContent=emailMsg._getMarketDataSuccessContent.format(self.srcMkt,self.srcType,self.dte,self.SH_mdMap_savecnt,self.SH_tsMap_savecnt,self.SH_indexMap_savecnt,self.CF_mdfMap_savecnt)

        if self.SH_mdMap_savecnt > 0:
            check_md_result=self.check_market_data(checkfilepathinfo)
            if len(check_md_result[0])>0:
                htmlContent = htmlContent+"<br>{0}</br>".format(check_mdf_result[0])
                errflag=True
            if len(check_md_result[1])>0:
                    htmlContent = htmlContent + emailMsg._checkMarketDataL2Content + emailMsg._checkMarketDataL2Table.format(check_md_result[1])

        if self.SH_tsMap_savecnt > 0:
            check_ts_result=self.check_transaction(checkfilepathinfo)
            if len(check_ts_result[0])>0:
                htmlContent = htmlContent+"<br>{0}</br>".format(check_mdf_result[0])
                errflag=True
            if len(check_ts_result[1])>0:
                htmlContent = htmlContent + emailMsg._checkTransactionContent + emailMsg._checkTransactionTable.format(check_ts_result[1])

        if self.SH_indexMap_savecnt > 0:
            check_index_result=self.check_index(checkfilepathinfo)
            if len(check_index_result[0])>0:
                htmlContent = htmlContent+"<br>{0}</br>".format(check_mdf_result[0])
                errflag=True
            if len(check_index_result[1])>0:
                htmlContent = htmlContent + emailMsg._checkIndexContent + emailMsg._checkIndexTable.format(check_index_result[1])

        if self.CF_mdfMap_savecnt > 0:
            check_mdf_result=self.check_market_data_futures(checkfilepathinfo)
            print check_mdf_result[0]
            if len(check_mdf_result[0])>0:
                htmlContent = htmlContent+"<br>{0}<br>".format(check_mdf_result[0])
                errflag=True
            if len(check_mdf_result[1])>0:
                if self.srcType.upper() == "L2":
                    htmlContent = htmlContent + emailMsg._checkCFL2Content + emailMsg._checkCFL2Table.format(check_mdf_result[1])
                elif self.srcType.upper() == "L1":
                    htmlContent = htmlContent + emailMsg._checkCFL1Content + emailMsg._checkCFL1Table.format(check_mdf_result[1])

        if errflag:
            emailTitle = emailMsg._getMarketDataExceptionTitle.format(self.srcMkt,self.srcType,self.dte)
        else:
            emailTitle = emailMsg._getMarketDataSuccessTitle.format(self.srcMkt,self.srcType,self.dte)

        emailContent = emailMsg._checkHtmlPre + emailMsg._checkHtmlLast.format(htmlContent)

        self.logger.info(emailContent)
        sendEmail(self.hdfemailinfo,emailTitle,' ',emailContent,0)

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
        self.login_hh_server(dte, hhip,hhport, hhuser, hhpwd, 0) # 0: 实时
        #self.on_amc()
        #self.on_check()

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
            if tkr == '000300': print tme
            v= (rv[1], rv[8], rv[2], rv[3], rv[4], rv[5], rv[6], rv[7])

            self.SH_indexMap.setdefault(tkr, []).append(v)

    def process_transaction(self, head, buf):
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

            v1 = [tme,rv[3], rv[4], rv[5], rv[6], rv[7], rv[48], rv[49], rv[50]]
            v1.extend(rv[8:48])
            v  = tuple(v1)
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

            v1= [rv[1], rv[4], rv[3], rv[5], rv[6], rv[7], rv[8], rv[9], rv[12], rv[14], rv[10], rv[11]]
            v1.extend(rv[19:39])
            v = tuple(v1)
            self.CF_mdfMap.setdefault(tkr, []).append(v)

    def on_exit(self):
        if self.recv_package_n == 0:
            print >>sys.stderr, 'exit: recv_k:', self.recv_k, 'recv_package_n:', self.recv_package_n
            self.reading = False 
            emailtitle = emailMsg._systemOnExitErrorTitle.format(self.srcMkt,self.srcType,self.dte)
            content=emailMsg._systemOnExitErrorContent.format(self.srcMkt,self.srcType,self.dte,5)
            sendEmail(self.hdfemailinfo,emailtitle,content,' ')
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
                    print >>sys.stderr, "recv hh response timeout,set timeout time is :%s " % (timeout)
                    # send email and the exit
                    emailtitle = emailMsg._timeoutErrorTitle.format(self.srcMkt,self.srcType,self.dte)
                    content=emailMsg._timeoutErrorContent.format(self.srcMkt,self.srcType,self.dte,timeout)
                    sendEmail(self.hdfemailinfo,emailtitle,content,' ')
                    self.logger.error("recvtimeout:{0}s,SystemExit.".format(timeout))
                    timeounterror="recv hh response timeout,{0},set timeout time is :{1}s ,headcontent:{2}".format(emailtitle,timeout,self.headcontent)
                    self.logger.error(timeounterror)
                    print "rec try"
                    # sys.exit(-1)
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
        self.r.publish(self.redis_stream_raw_key, (head, buf))
        self.r.rpush(self.redis_db_raw_key, (head, buf)) # TODO
        self.reading = False  #market close ,set recvFlag=false

    def process_market_overview(self,head,buf):
        self.r.publish(self.redis_stream_raw_key, (head, buf))
        self.r.rpush(self.redis_db_raw_key, (head, buf)) # TODO
        self.reading = False #market over view ,set recvFlag=false

    def check_market_data(self,checkfilepathinfo):
        checkTkr="{0}_CHECK_TKR".format(self.srcMkt.upper())
        #print "start transaction check:",checkfilepathinfo.get(checkTkr)
        orgtkrs = map(lambda x: x.strip(), open(checkfilepathinfo.get(checkTkr), 'r').readlines())
        checksresults=[]
        checksresults.append("")
        result=""
        for j in range(0,len(orgtkrs)):
            tkr=orgtkrs[j]
            fpath='/{0}_{1}_market_data/d{2}/t{3}'.format(self.srcMkt,self.srcType,self.dte,tkr)
            #print 'fpath:',fpath
            if fpath  not in self.h5file:
                continue
            try:
                tab=self.h5file.get_node(fpath)
                myrows=tab.nrows
                asize1=[ rec['asize1'] for rec in tab if (rec['tme']>=93000000) ]
                asize2=[ rec['asize2'] for rec in tab if (rec['tme']>=93000000) ]
                asize3=[ rec['asize3'] for rec in tab if (rec['tme']>=93000000) ]
                asize4=[ rec['asize4'] for rec in tab if (rec['tme']>=93000000) ]
                asize5=[ rec['asize5'] for rec in tab if (rec['tme']>=93000000) ]
                bsize1=[ rec['bsize1'] for rec in tab if (rec['tme']>=93000000) ]
                bsize2=[ rec['bsize2'] for rec in tab if (rec['tme']>=93000000) ]
                bsize3=[ rec['bsize3'] for rec in tab if (rec['tme']>=93000000) ]
                bsize4=[ rec['bsize4'] for rec in tab if (rec['tme']>=93000000) ]
                bsize5=[ rec['bsize5'] for rec in tab if (rec['tme']>=93000000) ]
                mytme=[ rec['tme'] for rec in tab if (rec['tme']>=93000000) ]
                avgasize1=round(np.mean(asize1),0)
                avgasize2=round(np.mean(asize2),0)
                avgasize3=round(np.mean(asize3),0)
                avgasize4=round(np.mean(asize4),0)
                avgasize5=round(np.mean(asize5),0)
                avgbsize1=round(np.mean(bsize1),0)
                avgbsize2=round(np.mean(bsize2),0)
                avgbsize3=round(np.mean(bsize3),0)
                avgbsize4=round(np.mean(bsize4),0)
                avgbsize5=round(np.mean(bsize5),0)
                mintme=np.min(mytme)
                maxtme=np.max(mytme)
                result += emailMsg._checkMarketDataL2Td.format(self.dte,tkr,myrows,mintme,maxtme,avgasize1,avgasize2,avgasize3,avgasize4,avgasize5,avgbsize1,avgbsize2,avgbsize3,avgbsize4,avgbsize5)
            except Exception,e:
                self.logger.error("check {0}_{1}_market_data_{2}_{3},Error:{4}".format(self.srcMkt,self.srcType,self.dte,tkr,e))
                #print "excep:",e
        checksresults.append(result)
        return checksresults

    def check_transaction(self,checkfilepathinfo):
        checkTkr="{0}_CHECK_TKR".format(self.srcMkt.upper())
        #print "start transaction check:",checkfilepathinfo.get(checkTkr)
        orgtkrs = map(lambda x: x.strip(), open(checkfilepathinfo.get(checkTkr), 'r').readlines())
        checksresults=[]
        checksresults.append("")
        result=""
        for j in range(0,len(orgtkrs)):
            tkr=orgtkrs[j]
            fpath='/{0}_{1}_transaction/d{2}/t{3}'.format(self.srcMkt,self.srcType,self.dte,tkr)
            #print 'fpath:',fpath
            if fpath  not in self.h5file:
                continue
            try:
                tab=self.h5file.get_node(fpath)
                myrows=tab.nrows
                qty=[ rec['qty'] for rec in tab if (rec['tme']>=93000000) ]
                mytme=[ rec['tme'] for rec in tab if (rec['tme']>=93000000) ]
                avgqty=round(np.mean(qty),0)
                mintme=np.min(mytme)
                maxtme=np.max(mytme)
                result += emailMsg._checkTransactionTd.format(self.dte,tkr,myrows,mintme,maxtme,avgqty)

            except Exception,e:
                self.logger.error("check {0}_{1}_transaction_{2}_{3},Error:{4}".format(self.srcMkt,self.srcType,self.dte,tkr,e))
                #print "excep:",e
        checksresults.append(result)
        return checksresults

    def check_index(self,checkfilepathinfo):
        checkTkr="{0}_CHECK_INDEX".format(self.srcMkt.upper())
        #print "start transaction check:",checkfilepathinfo.get(checkTkr)
        orgtkrs = map(lambda x: x.strip(), open(checkfilepathinfo.get(checkTkr), 'r').readlines())
        checksresults=[]
        checksresults.append("")

        result=""
        for j in range(0,len(orgtkrs)):
            tkr=orgtkrs[j]
            fpath='/{0}_{1}_index/d{2}/t{3}'.format(self.srcMkt,self.srcType,self.dte,tkr)
            #print 'fpath:',fpath
            if fpath  not in self.h5file:
                continue
            try:
                tab=self.h5file.get_node(fpath)
                myrows=tab.nrows
                volume=[ rec['volume'] for rec in tab if (rec['tme']>=93000000) ]
                mytme=[ rec['tme'] for rec in tab if (rec['tme']>=93000000) ]
                avgvolume=round(np.mean(volume),0)
                mintme=np.min(mytme)
                maxtme=np.max(mytme)
                result += emailMsg._checkIndexTd.format(self.dte,tkr,myrows,mintme,maxtme,avgvolume)
            except Exception,e:
                self.logger.error("check {0}_{1}_index_{2}_{3},Error:{4}".format(self.srcMkt,self.srcType,self.dte,tkr,e))
                #print "excep:",e
        checksresults.append(result)
        return checksresults

    def check_market_data_futures(self,checkfilepathinfo):
        checkTkr="{0}_CHECK_TKR".format(self.srcMkt.upper())
        #orgtkrs = map(lambda x: x.strip(), open('../config/IF.txt', 'r').readlines())
        orgtkrs = map(lambda x: x.strip(), open(checkfilepathinfo.get(checkTkr), 'r').readlines())
        print "orgtkrs",len(orgtkrs)
        checksresults=[]

        notkrs = []
        for otkrs in orgtkrs:
            tkrs=otkrs.split(' ')
            dtetkr=tkrs[0]
            if int(dtetkr) == int(self.dte):
                for i in range(1,len(tkrs)-1):
                    if tkrs[i] not in self.CF_mdfMap:
                        notkrs.append(tkrs[i])
                break
        if notkrs:
            checksresults.append("check {0}_{1}_market_data_futures_{2},Error:{3} is not exist".format(self.srcMkt,self.srcType,self.dte,notkrs))
        else:
            checksresults.append("")

        result=""

        for tkr in self.CF_mdfMap:
            fpath='/{0}_{1}_market_data_futures/d{2}/t{3}'.format(self.srcMkt,self.srcType,self.dte,tkr)
            print 'fpath:',fpath
            if fpath  not in self.h5file:
                #print 'no path'
                continue
            try:
                tab=self.h5file.get_node(fpath)
                myrows=tab.nrows
                mytme=[ rec['tme'] for rec in tab if (rec['tme']>=91500000) ]
                asize1=[ rec['asize1'] for rec in tab if (rec['tme']>=91500000) ]
                bsize1=[ rec['bsize1'] for rec in tab if (rec['tme']>=91500000) ]
                avgasize1=round(np.mean(asize1),0)
                avgbsize1=round(np.mean(bsize1),0)
                mintme=np.min(mytme)
                maxtme=np.max(mytme)

                if self.srcType.upper() == "L2":
                    asize2=[ rec['asize2'] for rec in tab if (rec['tme']>=91500000) ]
                    asize3=[ rec['asize3'] for rec in tab if (rec['tme']>=91500000) ]
                    asize4=[ rec['asize4'] for rec in tab if (rec['tme']>=91500000) ]
                    asize5=[ rec['asize5'] for rec in tab if (rec['tme']>=91500000) ]
                    bsize2=[ rec['bsize2'] for rec in tab if (rec['tme']>=91500000) ]
                    bsize3=[ rec['bsize3'] for rec in tab if (rec['tme']>=91500000) ]
                    bsize4=[ rec['bsize4'] for rec in tab if (rec['tme']>=91500000) ]
                    bsize5=[ rec['bsize5'] for rec in tab if (rec['tme']>=91500000) ]
                    avgasize2=round(np.mean(asize2),0)
                    avgasize3=round(np.mean(asize3),0)
                    avgasize4=round(np.mean(asize4),0)
                    avgasize5=round(np.mean(asize5),0)
                    avgbsize2=round(np.mean(bsize2),0)
                    avgbsize3=round(np.mean(bsize3),0)
                    avgbsize4=round(np.mean(bsize4),0)
                    avgbsize5=round(np.mean(bsize5),0)
                    result += emailMsg._checkCFL2Td.format(self.dte,tkr,myrows,mintme,maxtme,avgasize1,avgasize2,avgasize3,avgasize4,avgasize5,avgbsize1,avgbsize2,avgbsize3,avgbsize4,avgbsize5)
                else:
                    result += emailMsg._checkCFL1Td.format(self.dte,tkr,myrows,mintme,maxtme,avgasize1,avgbsize1)
            except Exception,e:
                self.logger.error("check {0}_{1}_market_data_{2}_{3},Error:{4}".format(self.srcMkt,self.srcType,self.dte,tkr,e))
                #print "excep:",e

        checksresults.append(result)

        return checksresults


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print >>sys.stderr, "usage:%s SH/SZ/CF L2/L1 dte,give 4 param." % (sys.argv[0])
        hdfemailinfo = gethdfemailinfo()
        send = sendEmail(hdfemailinfo,emailMsg._paramErrorTitle,emailMsg._paramErrorContent,'')
        sys.exit(-1)

    srcMkt  = sys.argv[1]
    srcType = sys.argv[2]
    dte     = int(sys.argv[3])

    tradedays = [int(x[0]) for x in [line.strip().split() for line in open('../config/calendar.txt')] if len(x) == 6]

    if dte not in tradedays:
        print >>sys.stderr, 'not tradeday, exit.'
        sys.exit(0)

    if srcMkt not in set(['SZ', 'SH', 'CF']):
        print >>sys.stderr, "usage:%s SH/SZ/CF L2/L1 dte" % (sys.argv[0])
        hdfemailinfo = gethdfemailinfo()
        send = sendEmail(hdfemailinfo,emailMsg._paramErrorTitle,emailMsg._paramErrorContent,'')
        sys.exit(-1)

    #mod by oliver 2013-08-29
    #hfs_online().run(srcType, dte)
    hfs_online().run(srcMkt,srcType, dte)
    #end mod by jwh 201308-29

