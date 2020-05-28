# -*- coding: utf-8 -*- #
import sys, os, datetime
import struct
import redis


class hfs_hh_parser(object):
    """ hfs hh struct parser """
    def __init__(self, dte, srcMkt, srcType):
        self.dte = dte
        self.srcMkt = srcMkt
        self.srcType = srcType
        self.gidMap = {}
        self.reading = True

        self.r = redis.Redis('192.168.1.16')
        self.ps = self.r.pubsub()

        self.redis_tkr_raw_key = 'TKRS_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType
        self.redis_db_raw_key = 'DB_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType
        self.redis_stream_raw_key = 'STREAM_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType
        self.redis_db_key = 'DB_HH' + '_' + self.srcMkt + '_' + self.srcType
        self.redis_stream_key = 'STREAM_HH' + '_' + self.srcMkt + '_' + self.srcType

    def on_bmo(self):
        # 删除redis数据缓存
        self.r.delete(self.redis_db_key)

    def on_amc(self):
        pass

    def on_message(self, head, body):
        if head[1] == 1012:
            self.process_market_data(head, body)
        elif head[1] == 1113:
            self.process_index(head, body)
        elif head[1] == 8:
            self.process_market_close(head, body)
        elif head[1] == 1115:
            self.process_market_overview(head, body)
        else:
            pass

    def load_code_table(self):
        """ process code mapping """
        buf = self.r.get(self.redis_tkr_raw_key)
        patstr = '<iiii' #codetable_head
        hlen = struct.calcsize(patstr)
        rv = struct.unpack(patstr, buf[0:hlen])
        enterdte = self.dte
        self.dte = rv[1]

        if int(enterdte) != int(self.dte):
            print "enter dte:",enterdte,"TDF dte:",self.dte
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
            name = rv[3].strip('\x00')
            self.gidMap[gid] = (symb, name, srcType)

    def process_index(self, head, buf):
        """ process index data """
        patstr = '<i'
        hlen = struct.calcsize(patstr)
        rv = struct.unpack(patstr, buf[0:hlen])
        N = rv[0]

        patstr = 'iiiiiiqqi'
        dlen = struct.calcsize(patstr)
        for i in range(N):
            rv = struct.unpack(patstr, buf[(hlen + dlen * i):(hlen + dlen * i + dlen)])
            gid, tme, opn, high, low, lastPx, volume, value, pclse = rv
            if gid not in self.gidMap: return
            tkr, tkrname, _ = self.gidMap[gid]

            opn = float(opn) / 1e4; high = float(high) / 1e4; low = float(low) / 1e4; 
            lastPx = float(lastPx) / 1e4; pclse = float(pclse) / 1e4; tme = float(tme) / 1e3
            # ntrade = totasize = totbsize = avgask = avgbid = iopv = yieldtm = ulmtpx = llmtpx = None # 匹配股票格式
            # ask = asize = bid = bsize = [None] # TODO: 指数数据包和股票数据包不同以减小网络带宽占用
            mdf = (tme, pclse, opn, high, low, lastPx, volume, value)
            self.r.publish(self.redis_stream_key, (tkr, mdf))
            self.r.rpush(self.redis_db_key, (tkr, mdf))

            obj = {}
            # obj = {'Dte':self.dte, 'Tme':tme, 'Tkr':tkr, 'PreClse':pclse, 'Vol':volume, 'Amt':value,\
            #        'Open':opn, 'High':high, 'Low':low, 'LastPrc':lastPx,\
            #        'NumTrade':ntrade, 'TotalAsize':totasize, 'TotalBsize':totbsize, \
            #        'AvgAsk':avgask, 'AvgBid':avgbid, 'IOPV':iopv, 'Yield':yieldtm,\
            #        'Ask':ask, 'Asize': asize, 'Bid':bid, 'Bsize':bsize,
            #        'UpLmtPrc':ulmtpx, 'LwLmtPrc':llmtpx}
            obj = {'Dte':self.dte, 'Tme':tme, 'Tkr':tkr, 'TkrName':tkrname, 'PreClse':pclse, 'Vol':volume, 'Amt':value,\
                   'Open':opn, 'High':high, 'Low':low, 'LastPrc':lastPx}
            obj['Tkr'] = obj['Tkr'] + '.' + self.srcMkt
            obj['UpdTme'] = self.conv_datetime(tme)
            self.r.set('QUOTES_%s' % obj['Tkr'], obj)
            
    def process_market_data(self, head, buf):
        """ process stock market data """
        patstr = '<' + 'i'*3 + 'I'*5 + 'I'*10 + 'I'*10 + 'I'*10 + 'I'*10 + 'I' + 'q'*4 + 'I'*2 + 'i'*2 + 'I'*2 + '4s'
        slen = struct.calcsize(patstr)
        
        N = struct.unpack('<i', buf[0:4])[0]

        for i in range(0, N):
            rv = struct.unpack(patstr, buf[(4+slen*i):(4+slen*(i+1))])
            gid, tme, status, pclse, opn, high, low, lastPx = rv[:8]
            if gid not in self.gidMap: continue
            tkr, tkrname, _ = self.gidMap[gid]

            ask = rv[8:18]; asize = rv[18:28]; bid = rv[28:38]; bsize = rv[38:48]; 
            ntrade, volume, value, totbsize, totasize, avgbid, avgask, iopv, yieldtm, ulmtpx, llmtpx, _ = rv[48:60]
            opn = float(opn) / 1e4; high = float(high) / 1e4; low = float(low) / 1e4; 
            lastPx = float(lastPx) / 1e4; pclse = float(pclse) / 1e4; tme = float(tme) / 1e3
            avgbid = float(avgbid) / 1e4; avgask = float(avgask) / 1e4; ulmtpx = float(ulmtpx) / 1e4; llmtpx = float(llmtpx) / 1e4
            ask = tuple([float(x) / 1e4 for x in ask])
            bid = tuple([float(x) / 1e4 for x in bid])
            mdf = (tme, pclse, opn, high, low, lastPx, volume, value, ulmtpx, llmtpx, \
                   ntrade, totasize, totbsize, avgask, avgbid, iopv, yieldtm, \
                   ask, asize, bid, bsize)
            self.r.publish(self.redis_stream_key, (tkr, mdf))
            self.r.rpush(self.redis_db_key, (tkr, mdf))

            obj = {}
            obj = {'Dte':self.dte, 'Tme':tme, 'Tkr':tkr, 'TkrName':tkrname, 'PreClse':pclse, 'Vol':volume, 'Amt':value,\
                   'Open':opn, 'High':high, 'Low':low, 'LastPrc':lastPx,\
                   'NumTrade':ntrade, 'TotalAsize':totasize, 'TotalBsize':totbsize, \
                   'AvgAsk':avgask, 'AvgBid':avgbid, 'IOPV':iopv, 'Yield':yieldtm,\
                   'Ask':ask, 'Asize': asize, 'Bid':bid, 'Bsize':bsize,
                   'UpLmtPrc':ulmtpx, 'LwLmtPrc':llmtpx}
            obj['Tkr'] = obj['Tkr'] + '.' + self.srcMkt
            obj['UpdTme'] = self.conv_datetime(tme)
            self.r.set('QUOTES_%s' % obj['Tkr'], obj)

    def process_market_close(self, head, buf):
        self.reading = False  #market close ,set recvFlag=false
        self.ps.unsubscribe()

    def process_market_overview(self, head, buf):
        self.reading = False #market over view ,set recvFlag=false
        self.ps.unsubscribe()

    def conv_datetime(self,tme):
        tme = str(tme).split('.')[0].rjust(6,'0') + '.' + str(tme).split('.')[1]
        return datetime.datetime.strptime('%d %s'%(self.dte, tme), '%Y%m%d %H%M%S.%f')

    def broadcast_history(self):
        for msg in self.r.lrange(self.redis_db_raw_key, 0, -1):
            self.on_message(*eval(msg))
        
    def subscribe_realtime(self):
        self.ps.subscribe(self.redis_stream_raw_key)
        for msg in self.ps.listen():
            if msg['type'] != 'message':
                continue
            self.on_message(*eval(msg['data']))

    def run(self):
        print "run dte: ", self.dte
        self.on_bmo()
        self.load_code_table()
        self.broadcast_history()
        self.subscribe_realtime()
        self.on_amc()

        
if __name__ == '__main__':

    if len(sys.argv) < 3:
        print >>sys.stderr, 'Usage: %s SH/SZ L1/L2 20170101' % sys.argv[0]
        sys.exit(-1)

    dte = int(sys.argv[3])
    srcMkt = sys.argv[1]
    srcType = sys.argv[2]

    tradedays = [int(x[0]) for x in [line.strip().split() for line in open('../config/calendar.txt')] if len(x) == 6]

    if dte not in tradedays:
        print >>sys.stderr, 'not tradeday, exit.'
        sys.exit(0)

    hfs_hh_parser(dte, srcMkt, srcType).run()

