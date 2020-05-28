import sys
import os
import datetime
import time
import pdb
import multiprocessing

def do_make(dte):
    os.system('../test make {}'.format(dte))

def run():
    import glob 
    dats = glob.iglob(r"/datas/share/stockdata/L2data/CF/*.dat")
    
    for dat in dats:
        dte = dat[7:15]
        print dte
        pdb.set_trace()
        do_make(dte)

if __name__ == '__main__':
    run()
    print 'done'
    