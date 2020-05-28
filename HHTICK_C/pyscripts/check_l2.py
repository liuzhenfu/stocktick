# -*- coding: utf-8 -*-
# @author: LZF
# @date: 2017.10.26

'''
读取从宏汇数据源获得的二进制文件
'''

from tick import *
import datetime, time, struct, os,pdb

from email.MIMEMultipart import  MIMEMultipart
from email.MIMEText import MIMEText
import smtplib


server = 'smtp.qiye.163.com'
user = 'operation@alpha2fund.com'
passwd = 'tms@2016'
send_to = ['liuzhenfu@alpha2fund.com']

def send_email(send_to, subject, content, fmt = 'plain'):
    try:
        COMMASPACE = ', '
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['To'] = COMMASPACE.join(send_to)
        msg.attach(MIMEText(content, fmt, 'utf-8'))

        smtp = smtplib.SMTP()
        smtp.connect(server)
        smtp.login(user, passwd)
        smtp.sendmail(user, send_to, msg.as_string())
        smtp.close()
        print "send success."
    except Exception, e:
        print "send fail.", e
class dataCheck():
    def __init__(self,path,dte):
        self.dte = dte
        self.fname = 'HHTICK_{}.dat'.format(dte)
        self.fname = os.path.join(path, self.fname)
        self.tkrs = {}
        self.tme = {'mkt_tme': {}, 'idx_tme': {}, 'od_tme': 0, 'ts_tme': 0, 'oq_tme':0 }
        self.cnt = {'mkt_cnt': 0, 'idx_cnt': 0, 'od_cnt': 0, 'ts_cnt': 0, 'oq_cnt':0, 'code_cnt':0 }
    def process_code_table(self,data):
        hlen = struct.calcsize(TDFDefine_SecurityCodeHead)
        head = data[0:hlen]
        source, dte, cnt, flag = struct.unpack(TDFDefine_SecurityCodeHead,head)
        # return cnt
        dlen = struct.calcsize(TDFDefine_SecurityCode)
        for i in range(cnt):
            rv = struct.unpack(TDFDefine_SecurityCode, data[hlen+dlen*i:hlen+dlen*(i+1)])
            # print rv[0], rv[2]
            self.tkrs[int(rv[0])] = rv[2][0:6]
        return cnt

    def process_market_data(self, data):
        hlen = struct.calcsize(TDFDefine_MarketDataHead)
        N = struct.unpack(TDFDefine_MarketDataHead, data[0:hlen])[0]
        
        dlen = struct.calcsize(TDFDefine_MarketData)
        for i in range(N):
            rv = struct.unpack(TDFDefine_MarketData, data[(hlen+dlen*i):(hlen+dlen*(i+1))])
            gid, tme, status, pclse, opn, high, low, lastPx = rv[:8]
            if gid not in self.tme['mkt_tme']:
                self.tme['mkt_tme'][gid] = 0
            if tme > (self.tme['mkt_tme'][gid]):
                self.tme['mkt_tme'][gid] = tme
        return N

    def process_index(self, data):
        hlen = struct.calcsize(TDFDefine_IndexDataHead)
        N = struct.unpack(TDFDefine_IndexDataHead, data[0:hlen])[0]
        # return N
        dlen = struct.calcsize(TDFDefine_IndexData)
        for i in range(N):
            rv = struct.unpack(TDFDefine_IndexData, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            gid, tme, opn, high, low, lastPx, volume, value, pclse = rv
            if gid not in self.tme['idx_tme']:
                self.tme['idx_tme'][gid] = 0
            if tme > (self.tme['idx_tme'][gid]):
                self.tme['idx_tme'][gid] = tme
        return N

    def process_transcation(self,data):
        hlen = struct.calcsize(TDFDefine_TransactionHead)
        N = struct.unpack(TDFDefine_TransactionHead, data[0:hlen])[1]
        dlen = struct.calcsize(TDFDefine_Transaction)
        for i in range(N):
            rv = struct.unpack(TDFDefine_Transaction, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tno = rv
            if tme > self.tme['ts_tme']:
                self.tme['ts_tme'] = tme
        return N

    def process_transcationex(self,data):
        hlen = struct.calcsize(TDFDefine_TransactionExHead)
        N = struct.unpack(TDFDefine_TransactionExHead, data[0:hlen])[1]
        dlen = struct.calcsize(TDFDefine_TransactionEx)
        for i in range(N):
            rv = struct.unpack(TDFDefine_TransactionEx, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tno = rv
            if tme > self.tme['ts_tme']:
                self.tme['ts_tme'] = tme
        return N

    def process_order(self, data):
        hlen = struct.calcsize(TDFDefine_OrderHead)
        N = struct.unpack(TDFDefine_OrderHead, data[0:hlen])[1]
        dlen = struct.calcsize(TDFDefine_Order)
        for i in range(N):
            rv = struct.unpack(TDFDefine_Order, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tp, flag, ch = rv
            if tme > self.tme['od_tme']:
                self.tme['od_tme'] = tme
        return N

    def process_order_queue(self, data):
        hlen = struct.calcsize(TDFDefine_OrderQueueHead)
        N = struct.unpack(TDFDefine_OrderQueueHead, data[0:hlen])[0]
        dlen = struct.calcsize(TDFDefine_OrderQueue)
        for i in range(N):
            rv = struct.unpack(TDFDefine_OrderQueue, data[(
                hlen + dlen * i):(hlen + dlen * i + dlen)])
            gid,tme, side, prc, ods, item,mx = rv
            if tme > self.tme['oq_tme']:
                self.tme['oq_tme'] = tme
        return N

    def check_data(self):
        try:
            bRight = True
            with open(self.fname,'rb') as pf:
                head_len = struct.calcsize(TDFDefine_MsgHead)
                while True:
                    msg_head = pf.read(head_len)
                    if len(msg_head) != head_len :
                        if len(msg_head) != 0:
                            ret = 'read head error: {}  {} '.format(len(msg_head), head_len)
                            bRight = False
                        break
                    flag, data_type, data_len,tme, n = struct.unpack(TDFDefine_MsgHead, msg_head)
                    body = pf.read(data_len)
                    if len(body) != data_len:
                        ret = 'read data error: {} {}'.format( len(body), data_len)
                        bRight = False
                        break
                    if data_type == 6:
                        self.cnt['code_cnt'] += self.process_code_table(body)
                    elif data_type == 1101: # 成交
                        self.cnt['ts_cnt'] += self.process_transcation(body)
                    elif data_type == 1102: # 委托队列
                        self.cnt['oq_cnt'] += self.process_order_queue(body)
                    elif data_type == 1103: # 逐笔委托
                        self.cnt['od_cnt'] += self.process_order(body)
                    elif data_type == 1012: # 十档行情
                        self.cnt['mkt_cnt'] += self.process_market_data(body)
                    elif data_type == 1113: # 指数
                        self.cnt['idx_cnt'] += self.process_index(body)
                    elif data_type == 1105: # 成交明细扩展
                        self.cnt['ts_cnt'] += self.process_transcationex(body)

            error_msg = ''
            for gid in self.tme['mkt_tme']:
                if self.tme['mkt_tme'][gid] < 150000:
                    error_msg += 'error : {} mkt tme {} < 150000\n'.format(self.tkrs[gid],self.tme['mkt_tme'][gid])
                    print error_msg
            for gid in self.tme['idx_tme']:
                if self.tme['idx_tme'][gid] < 150000:
                    error_msg += 'error : {} idx tme {} < 150000\n'.format(self.tkrs[gid],self.tme['idx_tme'][gid])
                    print error_msg
            ret = '''
                    合约数量:{}
                    十档挂单:{}万
                    成交明细:{}万
                    指数行情:{}万
                    委托队列:{}万
                    逐笔委托:{}万
                    成交时间:{}
                    委托时间:{}
                    逐笔时间:{}
                    '''
            ret = ret.format(
                self.cnt['code_cnt'], self.cnt['mkt_cnt'] / 10000, self.cnt['ts_cnt'] / 10000, self.cnt['idx_cnt'] / 10000, self.cnt['oq_cnt'] / 10000, self.cnt['od_cnt'] / 10000, self.tme['ts_tme'], self.tme['oq_tme'], self.tme['od_tme'])
            ret += error_msg
            return bRight, ret
        
        except Exception, e:
            import traceback
            print traceback.format_exc()
            send_email(send_to, u'{} L2行情检查异常！！！！'.format(dte), '')
            return False, ''
            # pdb.set_trace()
            # raise

def check(dte):
    bRight1, msg1 = dataCheck('../SH_N/', dte).check_data()
    bRight2, msg2 = dataCheck('../SZ_N/', dte).check_data()
    if not bRight1:
        send_email(send_to, u'{} SH L2行情检查失败!!!!'.format(dte), msg1)
    
    if not bRight2:
        send_email(send_to, u'{} SZ L2行情检查失败!!!!'.format(dte), msg2)
    
    if bRight1 and bRight2:
        send_email(send_to, u'{} L2行情检查结果'.format(dte), 'SH\n' + msg1 + 'SZ\n' + msg2)

if __name__ == '__main__':
    for dte in [20170710, 20170711, 20170712, 20170713, 20170714, 20170717, 20170718, 20170719, 20170720, 20170721]:
        check(dte)

