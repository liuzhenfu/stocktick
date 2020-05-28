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
import logger
import redis
import cx_Oracle

server = 'smtp.qiye.163.com'
user = 'operation@alpha2fund.com'
passwd = 'tms@2016'
send_to = ['liuzhenfu@alpha2fund.com','lvjieyong@alpha2fund.com','wangchao@alpha2fund.com','qiaochun@alpha2fund.com']
redis_ip = '192.168.1.16'
redis_port = 6379
oracle_ip = 'prodrw/rwprod@192.168.1.16:1521/orcl'

log = logger.get_logger('check_l2')

def hhmmssmss_2_s(tme):
    return tme / 10000000 * 60 * 60 + tme % 10000000 / 100000 * 60 + tme % 100000 / 1000

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
        self.error_msg = ''
        
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
            if int(source) == 0:
                self.tkrs_sz[int(rv[0])] = rv[2][0:6]
            else :
                self.tkrs_sh[int(rv[0])] = rv[2][0:6]
        return cnt
        
    def process_add_code(self,data):
        return 1
        
    def judge_tme(self, gid, tme):
        return 
        if gid in self.tkrs_sh.keys():
            if hhmmssmss_2_s(tme) - hhmmssmss_2_s(self.last_tme['sh']) < -3 and tme > 93000000:
                error = 'sh_exch_time error : gid:{}, tkr:{}, last_tme:{}, tme:{}'.format(gid, self.tkrs_sh[gid], self.last_tme['sh'], tme)
                log.info(error)
                self.error_msg = self.error_msg + error + '\n'
            self.last_tme['sh'] = tme 
        if gid in self.tkrs_sz.keys():
            if hhmmssmss_2_s(tme) - hhmmssmss_2_s(self.last_tme['sz']) < -3 and tme > 93000000:
                error = 'sz_exch_time error : gid:{}, tkr:{}, last_tme:{}, tme:{}'.format(gid, self.tkrs_sz[gid], self.last_tme['sz'], tme)
                log.info(error)
                self.error_msg = self.error_msg + error + '\n'
            self.last_tme['sz'] = tme 
        if hhmmssmss_2_s(tme) - hhmmssmss_2_s(max(self.last_tme['sh'], self.last_tme['sz'])) < -10 and tme > 93000000:
            error = 'tick_tme error : gid:{}, tkr:{}, last_tme:{}, tme:{}'.format(gid, self.tkrs[gid], max(self.last_tme['sh'], self.last_tme['sz']), tme)
            log.info(error)
            self.error_msg = self.error_msg + error + '\n'
            
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
            self.judge_tme(gid,tme)
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
            self.judge_tme(gid,tme)
        return N

    def process_transcation(self,data):
        hlen = struct.calcsize(TDFDefine_TransactionHead)
        gid,N = struct.unpack(TDFDefine_TransactionHead, data[0:hlen])
        dlen = struct.calcsize(TDFDefine_Transaction)
        for i in range(N):
            rv = struct.unpack(TDFDefine_Transaction, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tno = rv
            if tme > self.tme['ts_tme']:
                self.tme['ts_tme'] = tme
            self.judge_tme(gid,tme)
        return N

    def process_transcationex(self,data):
        hlen = struct.calcsize(TDFDefine_TransactionExHead)
        gid,N = struct.unpack(TDFDefine_TransactionExHead, data[0:hlen])
        dlen = struct.calcsize(TDFDefine_TransactionEx)
        for i in range(N):
            rv = struct.unpack(TDFDefine_TransactionEx, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tno, bs, odkd, funcode, res, ask, bid = rv
            if tme > self.tme['ts_tme']:
                self.tme['ts_tme'] = tme
            self.judge_tme(gid,tme)
        return N

    def process_order(self, data):
        hlen = struct.calcsize(TDFDefine_OrderHead)
        gid,N = struct.unpack(TDFDefine_OrderHead, data[0:hlen])
        dlen = struct.calcsize(TDFDefine_Order)
        for i in range(N):
            rv = struct.unpack(TDFDefine_Order, data[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            tme, idx, prc, vol, tp, flag, ch = rv
            if tme > self.tme['od_tme']:
                self.tme['od_tme'] = tme
            self.judge_tme(gid,tme)
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
            self.judge_tme(gid,tme)
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
                    elif data_type == 2001:
                        self.cnt['code_cnt'] += self.process_add_code(body)
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
            
            for gid in self.tme['mkt_tme']:
                if self.tme['mkt_tme'][gid] < 150000:
                    self.error_msg += 'error : {} mkt tme {} < 150000\n'.format(self.tkrs[gid],self.tme['mkt_tme'][gid])
                    print self.error_msg
            for gid in self.tme['idx_tme']:
                if self.tme['idx_tme'][gid] < 150000:
                    self.error_msg += 'error : {} idx tme {} < 150000\n'.format(self.tkrs[gid],self.tme['idx_tme'][gid])
                    print self.error_msg
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
            ret += self.error_msg
            self._to_oracle()
            return bRight, ret
        
        except Exception, e:
            import traceback
            print traceback.format_exc()
            send_email(send_to, u'{} L2行情检查异常！！！！'.format(self.dte), '')
            return False, ''
            # pdb.set_trace()
            # raise
    def _to_oracle(self):
        try:
            insert_sql = ''' insert into dailytickinfo(dte,type,count_tkr,count_md,count_ts,count_idx,count_oq,count_od,tme_md,tme_ts,tme_od,tme_oq,err_msg)
                             values({},{},{},{},{},{},{},{},{},{},{},{},'{}') '''
            #tme_error = self.error_msg.count('tick_tme error')
            #tme_error_sh = self.error_msg.count('sh_exch_time error')
            #tme_error_sz = self.error_msg.count('sz_exch_time error')
            err = ''#'tme_error:total:{},sh:{},sz:{}'.format(tme_error, tme_error_sh, tme_error_sz)
            insert_sql = insert_sql.format(self.dte,1 if self.fname.find("SH")!=-1 else 2, self.cnt['code_cnt'],
                                          self.cnt['mkt_cnt']/10000.0,self.cnt['ts_cnt']/10000.0, self.cnt['idx_cnt'] / 10000.0,
                                          self.cnt['oq_cnt'] / 10000.0, self.cnt['od_cnt'] / 10000.0, 
                                          0,self.tme['ts_tme'], self.tme['oq_tme'], self.tme['od_tme'],err)
            conn = cx_Oracle.connect(oracle_ip)
            cursor = conn.cursor()
            cursor.execute(insert_sql)
            conn.commit()                    
        except Exception, e:
            import traceback
            #pdb.set_trace()
            print traceback.format_exc()
            send_email(send_to, u'{} L2行情检查异常！！！！'.format(self.dte), '')
            return False, ''
def get_value(line,key):
    pos = line.find(key) + len(key) + 1
    pos_end = line.find(',', pos)
    return line[pos: pos_end]
    
def check(dte):
    bRight1, msg1 = dataCheck('../SH_N/', dte).check_data()
    bRight2, msg2 = dataCheck('../SZ_N/', dte).check_data()
    #return 
    #if not bRight1:
    #    send_email(send_to, u'{} SH L2行情检查失败!!!!'.format(dte), msg1)
    #
    #if not bRight2:
    #    send_email(send_to, u'{} SZ L2行情检查失败!!!!'.format(dte), msg2)
    #
    #if bRight1 and bRight2:
    #    send_email(send_to, u'{} L2行情检查结果'.format(dte), 'SH' + msg1 + '\nSZ' + msg2)
    conn = cx_Oracle.connect(oracle_ip)
    r = redis.Redis(redis_ip, redis_port)
    msg = r.get('REMOTE_DATA_CHECK_MSG')
    if msg != '':
        dte1 = int(get_value(msg,'file').split('/')[-1][0:-4])
        if dte1 != dte:
            send_email(send_to, u'{} L2Tick检查失败'.format(dte), '')
            return 
        tkr_cnt = int(get_value(msg,'tkr_cnt'))
        md_cnt = float(get_value(msg,'md_cnt'))
        ts_cnt = float(get_value(msg,'ts_cnt'))
        od_cnt = float(get_value(msg,'od_cnt'))
        idx_cnt = float(get_value(msg,'idx_cnt'))
        md_tme = int(get_value(msg,'md_tme'))
        ts_tme = int(get_value(msg,'ts_tme'))
        od_tme = int(get_value(msg,'od_tme'))
        #err_msg = get_value(msg,'err_msg')
        #tme_error = err_msg.count('last_tme[')
        #tme_error_sh = err_msg.count('last_tme_sh')
        #tme_error_sz = err_msg.count('last_tme_sz')
        tme_error = int(get_value(msg,'tme_error_all'))
        tme_error_sh = int(get_value(msg,'tme_error_sh'))
        tme_error_sz = int(get_value(msg,'tme_error_sz'))
        
        err = 'tme_error:total:{},sh:{},sz:{}'.format(tme_error, tme_error_sh, tme_error_sz)
        insert_sql = ''' insert into dailytickinfo(dte,type,count_tkr,count_md,count_ts,count_idx,count_oq,count_od,tme_md,tme_ts,tme_od,tme_oq,err_msg)
                             values({},{},{},{},{},{},{},{},{},{},{},{},'{}')'''
        insert_sql = insert_sql.format(dte,3, tkr_cnt,
                                      md_cnt,ts_cnt, idx_cnt, 0, od_cnt, 
                                      0,ts_tme, 0, od_tme,err)
        
        cursor = conn.cursor()
        cursor.execute(insert_sql)
        conn.commit()            
        #send_email(send_to, u'{} L2 TickPool检查结果'.format(dte), msg)
    import pandas as pd
    qry_sql = '''select dte, count_tkr, count_md, count_ts, count_idx, count_oq,count_od, tme_ts,tme_oq,err_msg from dailytickinfo where type={} and rownum < 5 order by dte desc'''
    df_sh = pd.read_sql(qry_sql.format( 1), conn)
    df_sz = pd.read_sql(qry_sql.format( 2), conn)
    df_tick = pd.read_sql(qry_sql.format( 3), conn)
    content = 'SH:\n' + df_sh.to_html() + '\nSZ:\n' + df_sz.to_html() + '\nTickPool:\n' + df_tick.to_html()
    send_email(send_to, u'{} L2 检查结果'.format(dte), content, 'html')
    
def check_c(dte):
    conn = cx_Oracle.connect(oracle_ip)
    root_path = '/datas/share/stockdata/L2data/'
    fname_sh = '{}SH_N/HHTICK_{}.dat'.format(root_path, dte)
    fname_sz = '{}SZ_N/HHTICK_{}.dat'.format(root_path, dte)
    os.system("./check.exe {}".format(fname_sh))
    log_name = 'TickDataCheck_{}.txt'.format(datetime.datetime.today().strftime('%Y-%m-%d'))
    f = open(log_name,'r')
    msg = f.readlines()[-1]
    print msg
    tkr_cnt = int(get_value(msg, 'tkr_cnt'))
    md_cnt = float(get_value(msg, 'md_cnt'))
    ts_cnt = float(get_value(msg, 'ts_cnt'))
    idx_cnt = float(get_value(msg, 'idx_cnt'))
    oq_cnt = float(get_value(msg, 'oq_cnt'))
    od_cnt = float(get_value(msg, 'od_cnt'))
    tme_ts = int(get_value(msg, 'tme_ts'))
    tme_od = int(get_value(msg, 'tme_od'))
    tme_oq = int(get_value(msg, 'tme_oq'))
    tme_error_total = int(get_value(msg, 'tme_error_total'))
    tme_error_sh = int(get_value(msg, 'tme_error_sh'))
    tme_error_sz = int(get_value(msg, 'tme_error_sz'))
    err = 'tme_error:total:{},sh:{},sz:{}'.format(tme_error_total, tme_error_sh, tme_error_sz)
    sql = ''' insert into dailytickinfo(dte,type,count_tkr,count_md,count_ts,count_idx,count_oq,count_od,tme_md,tme_ts,tme_od,tme_oq,err_msg)
                             values({},{},{},{},{},{},{},{},{},{},{},{},'{}')'''
    insert_sql = sql.format(dte,1, tkr_cnt,
                                  md_cnt,ts_cnt, idx_cnt, oq_cnt, od_cnt, 
                                  0,tme_ts, tme_od, tme_oq,err)
    cursor = conn.cursor()
    cursor.execute(insert_sql)
    conn.commit()
    
    os.system("./check.exe {}".format(fname_sz))
    log_name = 'TickDataCheck_{}.txt'.format(datetime.datetime.today().strftime('%Y-%m-%d'))
    f = open(log_name,'r')
    msg = f.readlines()[-1]
    print msg
    tkr_cnt = int(get_value(msg, 'tkr_cnt'))
    md_cnt = float(get_value(msg, 'md_cnt'))
    ts_cnt = float(get_value(msg, 'ts_cnt'))
    idx_cnt = float(get_value(msg, 'idx_cnt'))
    oq_cnt = float(get_value(msg, 'oq_cnt'))
    od_cnt = float(get_value(msg, 'od_cnt'))
    tme_ts = int(get_value(msg, 'tme_ts'))
    tme_od = int(get_value(msg, 'tme_od'))
    tme_oq = int(get_value(msg, 'tme_oq'))
    tme_error_total = int(get_value(msg, 'tme_error_total'))
    tme_error_sh = int(get_value(msg, 'tme_error_sh'))
    tme_error_sz = int(get_value(msg, 'tme_error_sz'))
    err = 'tme_error:total:{},sh:{},sz:{}'.format(tme_error_total, tme_error_sh, tme_error_sz)
    sql = ''' insert into dailytickinfo(dte,type,count_tkr,count_md,count_ts,count_idx,count_oq,count_od,tme_md,tme_ts,tme_od,tme_oq,err_msg)
                             values({},{},{},{},{},{},{},{},{},{},{},{},'{}')'''
    insert_sql = sql.format(dte,2, tkr_cnt,
                                  md_cnt,ts_cnt, idx_cnt, oq_cnt, od_cnt, 
                                  0,tme_ts, tme_od, tme_oq,err)
    cursor = conn.cursor()
    cursor.execute(insert_sql)
    conn.commit()    
    
    r = redis.Redis(redis_ip, redis_port)
    msg = r.get('REMOTE_DATA_CHECK_MSG')
    if msg != '':
        dte1 = int(get_value(msg,'file').split('/')[-1][0:-4])
        if dte1 != dte:
            send_email(send_to, u'{} L2TickPool检查失败'.format(dte), u'日期错误')
            return 
        tkr_cnt = int(get_value(msg,'tkr_cnt'))
        md_cnt = float(get_value(msg,'md_cnt'))
        ts_cnt = float(get_value(msg,'ts_cnt'))
        od_cnt = float(get_value(msg,'od_cnt'))
        idx_cnt = float(get_value(msg,'idx_cnt'))
        md_tme = int(get_value(msg,'md_tme'))
        ts_tme = int(get_value(msg,'ts_tme'))
        od_tme = int(get_value(msg,'od_tme'))

        tme_error = int(get_value(msg,'tme_error_all'))
        tme_error_sh = int(get_value(msg,'tme_error_sh'))
        tme_error_sz = int(get_value(msg,'tme_error_sz'))
        
        err = 'tme_error:total:{},sh:{},sz:{}'.format(tme_error, tme_error_sh, tme_error_sz)
        insert_sql = ''' insert into dailytickinfo(dte,type,count_tkr,count_md,count_ts,count_idx,count_oq,count_od,tme_md,tme_ts,tme_od,tme_oq,err_msg)
                             values({},{},{},{},{},{},{},{},{},{},{},{},'{}')'''
        insert_sql = insert_sql.format(dte,3, tkr_cnt,
                                      md_cnt,ts_cnt, idx_cnt, 0, od_cnt, 
                                      0,ts_tme, od_tme, 0,err)
        
        cursor = conn.cursor()
        cursor.execute(insert_sql)
        conn.commit()            
        #send_email(send_to, u'{} L2 TickPool检查结果'.format(dte), msg)
    import pandas as pd
    qry_sql = '''select dte, count_tkr, count_md, count_ts, count_idx, count_oq,count_od, tme_ts,tme_od,err_msg from dailytickinfo where type={} and rownum < 5 order by dte desc'''
    df_sh = pd.read_sql(qry_sql.format( 1), conn)
    df_sz = pd.read_sql(qry_sql.format( 2), conn)
    df_tick = pd.read_sql(qry_sql.format( 3), conn)
    content = 'SH:\n' + df_sh.to_html() + '\nSZ:\n' + df_sz.to_html() + '\nTickPool:\n' + df_tick.to_html()
    send_email(send_to, u'{} L2 检查结果'.format(dte), content, 'html')
    
if __name__ == '__main__':
    #20171016,20171017,20171018,20171019,20171020,20171023,20171024,20171025,20171026,20171027,20171101,20171102,20171103,20171106,20171107,20171108,20171109,20171110,20171113,20171114,20171115
 
    check_c(20180510)

    

