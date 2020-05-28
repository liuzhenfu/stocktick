# -*- coding: utf-8 -*- #
import sys, os, datetime
import tables
import numpy as np
import pandas as pd
from hdfdefines import *
from hfsutils import *


class hfs_hh_check(object):
    """ hfs hh data archive check """
    def __init__(self, dte, srcMkt, srcType):
        self.dte = dte
        self.srcMkt = srcMkt
        self.srcType = srcType

        self.h5file = tables.open_file('../data/HH_TICKDB.h5','r')

        style = open('../config/style.css').read()
        self.check_report = style + u'<h1>数据检查报告(日期-{}, 市场-{}, 类型-{})</h1>'.format(self.dte, self.srcMkt, self.srcType)

    def check_market_data(self):
        orgtkrs = [x.strip() for x in open('../config/{}tkrs.txt'.format(self.srcMkt.lower()))]
        report  = []
        for tkr in orgtkrs:
            fpath = '/{0}_{1}_market_data/d{2}/t{3}'.format(self.srcMkt,self.srcType,self.dte,tkr)
            try:
                table = self.h5file.get_node(fpath)
                myrows = table.nrows
                asize1 = [ rec['asize1'] for rec in table if (rec['tme']>=93000000) ]
                asize2 = [ rec['asize2'] for rec in table if (rec['tme']>=93000000) ]
                asize3 = [ rec['asize3'] for rec in table if (rec['tme']>=93000000) ]
                asize4 = [ rec['asize4'] for rec in table if (rec['tme']>=93000000) ]
                asize5 = [ rec['asize5'] for rec in table if (rec['tme']>=93000000) ]
                bsize1 = [ rec['bsize1'] for rec in table if (rec['tme']>=93000000) ]
                bsize2 = [ rec['bsize2'] for rec in table if (rec['tme']>=93000000) ]
                bsize3 = [ rec['bsize3'] for rec in table if (rec['tme']>=93000000) ]
                bsize4 = [ rec['bsize4'] for rec in table if (rec['tme']>=93000000) ]
                bsize5 = [ rec['bsize5'] for rec in table if (rec['tme']>=93000000) ]
                mytme  = [ rec['tme']    for rec in table if (rec['tme']>=93000000) ]
                avgasize1 = round(np.mean(asize1),0)
                avgasize2 = round(np.mean(asize2),0)
                avgasize3 = round(np.mean(asize3),0)
                avgasize4 = round(np.mean(asize4),0)
                avgasize5 = round(np.mean(asize5),0)
                avgbsize1 = round(np.mean(bsize1),0)
                avgbsize2 = round(np.mean(bsize2),0)
                avgbsize3 = round(np.mean(bsize3),0)
                avgbsize4 = round(np.mean(bsize4),0)
                avgbsize5 = round(np.mean(bsize5),0)
                mintme = np.min(mytme)
                maxtme = np.max(mytme)
                report.append((self.dte, tkr, myrows, mintme, maxtme, avgasize1, avgasize2, avgasize3, avgasize4, avgasize5, avgbsize1, avgbsize2, avgbsize3, avgbsize4, avgbsize5))
            except Exception,e:
                print >>sys.stderr, "check {0}_{1}_market_data_{2}_{3},Error:{4}".format(self.srcMkt,self.srcType,self.dte,tkr,e)

        df = pd.DataFrame(report, columns = [u'日期', u'股票代码', u'数据条数', u'开始时间', u'结束时间', u'卖1均量', u'卖2均量', u'卖3均量', u'卖4均量', u'卖5均量', u'买1均量', u'买2均量', u'买3均量', u'买4均量', u'买5均量'])
        self.check_report += u'<h2>股票数据报告: </h2>' + df.to_html(index = False)

    def check_index(self):
        orgtkrs = [x.strip() for x in open('../config/{}index.txt'.format(self.srcMkt.lower()))]
        report  = []
        for tkr in orgtkrs:
            fpath='/{0}_{1}_index/d{2}/t{3}'.format(self.srcMkt,self.srcType,self.dte,tkr)
            try:
                table = self.h5file.get_node(fpath)
                myrows = table.nrows
                volume = [ rec['volume'] for rec in table if (rec['tme']>=93000000) ]
                mytme  = [ rec['tme']    for rec in table if (rec['tme']>=93000000) ]
                avgvolume = round(np.mean(volume),0)
                mintme = np.min(mytme)
                maxtme = np.max(mytme)
                report.append((self.dte, tkr, myrows, mintme, maxtme, avgvolume))
            except Exception,e:
                print >>sys.stderr, "check {0}_{1}_index_{2}_{3},Error:{4}".format(self.srcMkt,self.srcType,self.dte,tkr,e)

        df = pd.DataFrame(report, columns = [u'日期', u'指数代码', u'数据条数', u'开始时间', u'结束时间', u'平均成交量'])
        self.check_report += u'<h2>指数数据报告: </h2>' + df.to_html(index = False)

    def save_report(self):
        path = '../report/{}/'.format(self.dte)
        if not os.path.exists(path): os.makedirs(path)
        f = open(path + '{}{}.html'.format(self.srcMkt, self.srcType), 'w')
        f.write(self.check_report.encode('utf8'))
        f.close()

    def run(self):
        print 'check index...'
        self.check_index()
        print 'check market data...'
        self.check_market_data()
        print 'save report...'
        self.save_report()
        print 'all done.'


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

    hfs_hh_check(dte, srcMkt, srcType).run()
