# -*- coding: utf-8 -*- #
import sys, os, datetime
import tables
import leveldb
import struct
from collections import defaultdict
from hfsutils import *
from hdfdefines import market_data, market_index


class hfs_hh_archiver(object):
    """ archive hfs tick data to hdf5 """
    def __init__(self, dte, srcMkt, srcType):
        self.dte = dte
        self.srcMkt = srcMkt
        self.srcType = srcType
        self.gidMap = {}
        self.indexMap = defaultdict(list)
        self.mdMap = defaultdict(list)

        FILTERS = tables.Filters(complib = 'zlib', complevel = 9)
        self.h5file = tables.open_file('../data/HH_TICKDB.h5', mode = 'a',  filters = FILTERS, title = 'hfs data db file')
        self.db = leveldb.LevelDB('../data/{0}/{1}{2}'.format(dte, srcMkt, srcType))

    def process_code_table(self, buf):
        patstr = '<iiii' # codetable_head
        hlen = struct.calcsize(patstr)
        rv = struct.unpack(patstr, buf[0:hlen])
        enterdte = self.dte
        self.dte = rv[1]

        if int(enterdte) != int(self.dte):
            print >>sys.stderr, "enter dte: ", enterdte, "TDF dte: ", self.dte
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
            self.gidMap[gid] = (symb, name, srcType)

    def process_index(self, buf):
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
            v = (tme, rv[8], rv[2], rv[3], rv[4], rv[5], rv[6], rv[7])
            self.indexMap[tkr].append(v)

    def process_market_data(self, buf):
        patstr = '<' + 'i'*3 + 'I'*5 + 'I'*10 + 'I'*10 + 'I'*10 + 'I'*10 + 'I' + 'q'*4 + 'I'*2 + 'i'*2 + 'I'*2 + '4s'
        slen = struct.calcsize(patstr)

        N = struct.unpack('<i', buf[0:4])[0]
        for i in range(0, N):
            rv = struct.unpack(patstr, buf[(4+slen*i):(4+slen*(i+1))])
            gid = rv[0]
            tme = rv[1]
            if gid not in self.gidMap: continue

            tkr = self.gidMap[gid][0]
            v = tuple([tme,rv[3], rv[4], rv[5], rv[6], rv[7], rv[48], rv[49], rv[50]] + list(rv[8:48]))
            self.mdMap[tkr].append(v)

    def save_md(self):
        gname = '/%s_%s_market_data/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt = 0
        for tkr in self.mdMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.remove_node(gname, name)
                print 'remove md', gname, name

            table = self.h5file.create_table(gname, 't%s'%(tkr), market_data, 'market data', \
                                            expectedrows=4500, createparents=True)
            md    = table.row
            for x in self.mdMap[tkr]:
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

    def save_index(self):
        gname = '/%s_%s_index/d%d' % (self.srcMkt, self.srcType, self.dte)
        cnt = 0
        for tkr in self.indexMap:
            name = 't%s'%(tkr)
            path = '%s/%s' %(gname, name)
            if path in self.h5file:
                self.h5file.remove_node(gname, name)
                print 'remove index', gname, name

            table = self.h5file.create_table(gname, name, market_index, 'index data', \
                                            expectedrows=10000, createparents=True)
            mindex  = table.row
            for x in self.indexMap[tkr]:
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

    def archive(self):
        # read and parse tick
        print datetime.datetime.now(), "start broadcast history..."
        for key, msg in self.db.RangeIter():
            if int(key) == 0:  # the first key is code table
                self.process_code_table(msg)
                continue
            head, body = eval(msg)
            if head[1] == 1012:
                self.process_market_data(body)
            elif head[1] == 1113:
                self.process_index(body)

        # save to hdf5
        print datetime.datetime.now(), "start dump index..."
        self.save_index()
        print datetime.datetime.now(), "start dump market data..."
        self.save_md()
        print datetime.datetime.now(), "all done."


if __name__ == '__main__':

    if len(sys.argv) != 4:
        print >>sys.stderr, "usage:%s SH/SZ/CF L2/L1 dte,give 4 param." % (sys.argv[0])
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
        sys.exit(-1)

    hfs_hh_archiver(dte, srcMkt, srcType).archive()

