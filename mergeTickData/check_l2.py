# -*- coding: utf-8 -*-
# @author: LZF
# @date: 2017.10.26

'''
读取从宏汇数据源获得的二进制文件
'''

from tick import *
import datetime, time, struct, os,pdb

#from email.MIMEMultipart import  MIMEMultipart
#from email.MIMEText import MIMEText
#import smtplib
import logger

server = 'smtp.qiye.163.com'
user = 'operation@alpha2fund.com'
passwd = 'tms@2016'
send_to = ['liuzhenfu@alpha2fund.com']

log = logger.get_logger('check_l2')

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
        self.tkrs_sh = {}
        self.tkrs_sz = {}
        self.tme = {'mkt_tme': {}, 'idx_tme': {}, 'od_tme': 0, 'ts_tme': 0, 'oq_tme':0 }
        self.cnt = {'mkt_cnt': 0, 'idx_cnt': 0, 'od_cnt': 0, 'ts_cnt': 0, 'oq_cnt':0, 'code_cnt':0 }
        self.last_tme = {'sh':0, 'sz':0}
        
    def process_code_table(self,data):
        hlen = struct.calcsize(TDFDefine_SecurityCodeHead)
        head = data[0:hlen]
        source, dte, cnt, flag = struct.unpack(TDFDefine_SecurityCodeHead,head)
        # return cnt
        dlen = struct.calcsize(TDFDefine_SecurityCode)
        for i in range(cnt):
            rv = struct.unpack(TDFDefine_SecurityCode, data[hlen+dlen*i:hlen+dlen*(i+1)])
            gid, type, code, symbol = rv
            self.tkrs[int(rv[0])] = rv[2][0:6]
            if int(source) == 0:
                self.tkrs_sz[int(rv[0])] = rv[2][0:6]
            else :
                self.tkrs_sh[int(rv[0])] = rv[2][0:6]
        return cnt
    def process_add_code(self,data):
        hlen = struct.calcsize(TDFDefine_SecurityCodeHead)
        head = data[0:hlen]
        source, dte, cnt, flag = struct.unpack(TDFDefine_SecurityCodeHead,head)
        # return cnt
        dlen = struct.calcsize(TDFDefine_SecurityCode)
        for i in range(cnt):
            rv = struct.unpack(TDFDefine_SecurityCode, data[hlen+dlen*i:hlen+dlen*(i+1)])
            gid, type, code, symbol = rv
            self.tkrs[int(rv[0])] = rv[2][0:6]
            if int(source) == 0:
                self.tkrs_sz[int(rv[0])] = rv[2][0:6]
            else :
                self.tkrs_sh[int(rv[0])] = rv[2][0:6]
        return cnt
         
    def judge_tme(self, gid, tme):
        if gid in self.tkrs_sh.keys():
            if tme - self.last_tme['sh'] <= -3000 and tme > 93000000:
                log.info('sh_exch_time error : gid:{}, tkr:{}, last_tme:{}, tme:{}'.format(gid, self.tkrs_sh[gid], self.last_tme['sh'], tme))
            self.last_tme['sh'] = tme 
        if gid in self.tkrs_sz.keys():
            if tme - self.last_tme['sz'] <= -3000 and tme > 93000000:
                log.info('sz_exch_time error : gid:{}, tkr:{}, last_tme:{}, tme:{}'.format(gid, self.tkrs_sz[gid], self.last_tme['sz'], tme))
            self.last_tme['sz'] = tme 
        if tme - max(self.last_tme['sh'], self.last_tme['sz']) <= -10000 and tme > 93000000:
            log.info('tick_tme error : gid:{}, tkr:{}, last_tme:{}, tme:{}'.format(gid, self.tkrs[gid], max(self.last_tme['sh'], self.last_tme['sz']), tme))
    
    def process_market_data(self, data):
        hlen = struct.calcsize(TDFDefine_MarketDataHead)
        N = struct.unpack(TDFDefine_MarketDataHead, data[0:hlen])[0]
        
        dlen = struct.calcsize(TDFDefine_MarketData)
        for i in range(N):
            rv = struct.unpack(TDFDefine_MarketData, data[(hlen+dlen*i):(hlen+dlen*(i+1))])
            gid, tme, status, pclse, opn, high, low, lastPx = rv[:8]
            if tme == 0:
                pdb.set_trace()
            if gid not in self.tme['mkt_tme']:
                self.tme['mkt_tme'][gid] = 0
            if tme > (self.tme['mkt_tme'][gid]):
                self.tme['mkt_tme'][gid] = tme
            self.judge_tme(gid, tme)
        return N

    def process_index(self, data):
        hlen = struct.calcsize(TDFDefine_IndexDataHead)
        N = struct.unpack(TDFDefine_IndexDataHead, data[0:hlen])[0]
        # return N
        dlen = struct.calcsize(TDFDefine_IndexData)
        for i in range(N):
            rv = struct.unpack(TDFDefine_IndexData, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            gid, tme, opn, high, low, lastPx, volume, value, pclse = rv
            if tme == 0:
                pdb.set_trace()
            if gid not in self.tme['idx_tme']:
                self.tme['idx_tme'][gid] = 0
            if tme > (self.tme['idx_tme'][gid]):
                self.tme['idx_tme'][gid] = tme
            #self.judge_tme(gid, tme)
        return N

    def process_transcation(self,data):
        hlen = struct.calcsize(TDFDefine_TransactionHead)
        gid,N = struct.unpack(TDFDefine_TransactionHead, data[0:hlen])
        dlen = struct.calcsize(TDFDefine_Transaction)
        for i in range(N):
            rv = struct.unpack(TDFDefine_Transaction, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tno = rv
            if tme == 0:
                pdb.set_trace()
            if tme > self.tme['ts_tme']:
                self.tme['ts_tme'] = tme
            #self.judge_tme(gid, tme)
        return N

    def process_transcationex(self,data):
        try:
            hlen = struct.calcsize(TDFDefine_TransactionExHead)
            gid,N = struct.unpack(TDFDefine_TransactionExHead, data[0:hlen])
            dlen = struct.calcsize(TDFDefine_TransactionEx)
            for i in range(N):
                rv = struct.unpack(TDFDefine_TransactionEx, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
                tme, idx, prc, vol, tno, bs, odkd, funcode, res, ask, bid = rv
                if tme == 0:
                    pdb.set_trace()
                if tme > self.tme['ts_tme']:
                    self.tme['ts_tme'] = tme
                #self.judge_tme(gid, tme)
            return N
        except Exception, e:
            import traceback
            print traceback.format_exc()        
            pdb.set_trace()

    def process_order(self, data):
        hlen = struct.calcsize(TDFDefine_OrderHead)
        gid,N = struct.unpack(TDFDefine_OrderHead, data[0:hlen])
        dlen = struct.calcsize(TDFDefine_Order)
        for i in range(N):
            rv = struct.unpack(TDFDefine_Order, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tp, flag, ch = rv
            if tme == 0:
                pdb.set_trace()
            if tme > self.tme['od_tme']:
                self.tme['od_tme'] = tme
            #self.judge_tme(gid, tme)
        return N

    def process_order_queue(self, data):
        hlen = struct.calcsize(TDFDefine_OrderQueueHead)
        N = struct.unpack(TDFDefine_OrderQueueHead, data[0:hlen])[0]
        dlen = struct.calcsize(TDFDefine_OrderQueue)
        for i in range(N):
            rv = struct.unpack(TDFDefine_OrderQueue, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            gid,tme, side, prc, ods, item,mx = rv
            if tme == 0:
                continue
            if tme > self.tme['oq_tme']:
                self.tme['oq_tme'] = tme
            #self.judge_tme(gid, tme)
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
                    #elif data_type == 2001:
                        #self.process_add_code(body)
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
                self.cnt['code_cnt'], self.cnt['mkt_cnt'] / 10000.0, self.cnt['ts_cnt'] / 10000.0, self.cnt['idx_cnt'] / 10000.0, self.cnt['oq_cnt'] / 10000.0, self.cnt['od_cnt'] / 10000.0, self.tme['ts_tme'], self.tme['oq_tme'], self.tme['od_tme'])
            ret += error_msg
            return bRight, ret
        
        except Exception, e:
            import traceback
            print traceback.format_exc()
            send_email(send_to, u'{} L2行情检查异常！！！！'.format(self.dte), '')
            return False, ''
            # pdb.set_trace()
            # raise

def check(dte):
    log.info('start check {}'.format(dte))
    bRight, msg = dataCheck('../../SZ_N/', dte).check_data()
    log.info(msg)

if __name__ == '__main__':
    dte = 20180410
    import sys
    if len(sys.argv) > 1:
        dte = int(sys.argv[1])
    check(20180410)

