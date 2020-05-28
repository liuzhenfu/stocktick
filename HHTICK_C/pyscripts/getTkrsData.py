import os
import datetime
import pdb
import pexpect
import time

tkrs = ["000166",
"000403",
"000622",
"000627",
"000670",
"000693",
"000831",
"002274",
"002687",
"600059",
"600145",
"600483",
"600603",
"600795",
"600817",]


start = 20140101
end = 20140611

def createDir(dte):
    rootdir = "../data/2015/"
    for tkr in tkrs:
        datapath = os.path.join(rootdir, tkr, str(dte))
        if not os.path.exists(datapath):
            os.makedirs(datapath) 

def down_one(dte):
    createDir(dte)
    cmd = '../bin/HHTick ../config/config_36_SH.xml {}'.format(dte)
    child = pexpect.spawn(cmd)
    while True:
        process = child.readline()
        print(process)
        if process == "":
            pdb.set_trace()
        if process.find('quit') != -1:
            print('down load SH L2 done')
            #time.sleep(5)
            child.sendcontrol('c')
            break
        elif process.find('Connection refused') != -1 or process.find('Connection reset') != -1:
            return -1
    
    #return 0
    cmd = '../bin/HHTick ../config/config_36_SZ.xml {}'.format(dte)
    child = pexpect.spawn(cmd)
    while True:
        process = child.readline()
        print(process)
        if process.find('quit') != -1:
            print('down load SZ L2 done')
            #time.sleep(5)
            child.sendcontrol('c') 
            break
        elif process.find('Connection refused') != -1 or process.find('Connection reset') != -1:
            break
def run():
    #downlist = [x.strip('\n') for x in open('./downlist.txt','r').readlines()]
    downlist = filter(lambda x: int(x[0])>=start and int(x[0])<=end and len(x)==6,[x.strip().split() for x in open('./calendar.txt').readlines()])
    tme = int(datetime.datetime.now().strftime("%H%M%S"))
    while tme <= 82500 or tme > 90000:        
        print downlist[-1][0]
        if down_one(downlist[-1][0]) == -1:
            return 
        downlist = downlist[0:-1]
        #open('./downlist.txt','w').write(' '.join(downlist))
        #time.sleep(2)
        #time.sleep(5*60)
        tme = int(datetime.datetime.now().strftime("%H%M%S"))           
                    

if __name__ == '__main__':
    run()



