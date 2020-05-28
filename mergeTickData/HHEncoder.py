import sys
import os
import datetime
import time
import pdb
import multiprocessing

def encoder(dte):
    #pdb.set_trace()
    fname = '/datas/share/stockdata/L2data/SZ_N/HHTICK_{}.dat'.format(dte)
    ofname = '/datas/share/bar_data/stock_bar_data/TickPool/SZ_N/SZ_{}.dat'.format(dte)
    # cfname = './config.xml'
    opt = 'make'
    os.system('../StkTick/HHEncoder.exe {} {} {}'.format(opt, fname, ofname))


def describe(dte):
    fname = '/datas/share/stockdata/L2data/SZ_N/HHTICK_{}.dat'.format(dte)
    ofname = '/datas/share/bar_data/stock_bar_data/TickPool/SZ_N/SZ_{}.dat'.format(dte)
    # cfname = './config.xml'
    opt = 'describe'
    os.system('../StkTick/HHEncoder.exe {} {}'.format(opt, ofname))

def read(dte):
    fname = '/datas/share/stockdata/L2data/SZ_N/HHTICK_{}.dat'.format(dte)
    ofname = '/datas/share/bar_data/stock_bar_data/TickPool/SZ_N/SZ_{}.dat'.format(dte)
    # cfname = './config.xml'
    opt = 'read'
    os.system('../StkTick/HHEncoder.exe {} {}'.format(opt, ofname))

def stkTick(opt, fname, ofname):
    os.system('../StkTick/HHEncoder.exe {} {} {}'.format(opt, fname,ofname))

def run(dats):
    for dat in dats:
        dte = dat[-12:-4]
        print dte
        fname = dat
        ofname = '/datas/share/bar_data/stock_bar_data/TickPool/SZ/SZ_{}.dat'.format(dte)
        stkTick('make', dat, ofname)
        # stkTick('describe', '', ofname)

if __name__ == '__main__':
    #20171018, 20171019, 20171020, 20171023, 20171024, 20171025, 20171026, 20171027, 20171030,  20171031, 20171101, 20171102, 20171103, 20171106, 20171107
    # for dte in [20171117]:
    #     print dte
        # describe(dte)
        # encoder(dte)
        # read(dte)
    import glob 
    dats = glob.iglob(r"/datas/share/stockdata/L2data/SZ_N/*.dat")
    process = []
    for i in range(0,len(dats),2):
        p = multiprocessing.Process(target=run, args=(dats[i:i+2]))
        process.append(p)
    
    for p in process:
        p.start()

    # for dat in dats:
    #     dte = dat[-12:-4]
    #     print dte
    #     fname = dat
    #     ofname = '/datas/share/bar_data/stock_bar_data/TickPool/SZ/SZ_{}.dat'.format(dte)
    #     stkTick('make', dat, ofname)
        # stkTick('describe', '', ofname)
    # dte = 20170907
    # fname = '/datas/share/stockdata/L2data/SZ_N/HHTICK_20170907.dat'
    # ofname = '/datas/share/bar_data/stock_bar_data/TickPool/SZ/SZ_{}.dat'.format(dte)
    # stkTick('make', fname, ofname)

    print 'done'
