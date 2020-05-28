# -*- coding: utf-8 -*- #
import sys, os, datetime, shutil
import struct
import redis
import leveldb


class hfs_hh_dumper(object):
    """ hfs hh raw data dumper """
    def __init__(self, dte, srcMkt, srcType):
        self.dte = dte
        self.srcMkt = srcMkt
        self.srcType = srcType

        self.r = redis.Redis('192.168.1.16')
        self.ps = self.r.pubsub()

        self.redis_tkr_raw_key = 'TKRS_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType
        self.redis_stream_raw_key = 'STREAM_HH_RAW' + '_' + self.srcMkt + '_' + self.srcType

        self.db = None
        self.keyid = 0

    def on_message(self, msg):
        " write to leveldb, key auto increasement """
        self.db.Put(str(self.keyid).zfill(12), msg) # zfill(12) enough to handle 1e7 keys/s (~100ns)
        self.keyid += 1

    def run(self):
        # create leveldb
        dbname = '../data/{0}/{1}{2}'.format(self.dte, self.srcMkt, self.srcType)
        if os.path.exists(dbname):
            shutil.rmtree(dbname)
        os.makedirs(dbname)
        self.db = leveldb.LevelDB(dbname)

        # process code table
        buf = self.r.get(self.redis_tkr_raw_key)
        self.on_message(buf)

        # process market data 
        self.ps.subscribe(self.redis_stream_raw_key)
        for msg in self.ps.listen():
            if msg['type'] != 'message':
                continue
            head, _ = eval(msg['data'])
            if head[1] == 8 or head[1] == 1115: 
                self.ps.unsubscribe() 
                break # 收市信息不写入leveldb
            self.on_message(msg['data'])


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

    hfs_hh_dumper(dte, srcMkt, srcType).run()
