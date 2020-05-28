# -*- coding: utf-8 -*- #
import datetime
import os
import pdb
import pexpect
import sys
import time
from hdfgetL2 import down_load_l2
import redis

host = '172.18.94.223'
user = 'root'
passwd = '123456'
remote_redis_ip = '172.18.94.127'
remote_redis_port = 8080
local_redis_ip = '192.168.1.16'
local_redis_port = 6379

def ssh_login(host, user, passwd):
    cmd = 'ssh {}@{}'.format(user, host)
    child = pexpect.spawn(cmd)
    index = child.expect(['(?i)password', pexpect.EOF, pexpect.TIMEOUT])
    if index != 0:
        print ('ssh connect failed')
        child.close(force=True)
        return None
    child.sendline(passwd)
    index = child.expect([user, 'try again'])
    if index == 1:
        print('passwd error')
        return None
    print('ssh login success')
    return child


def do_download(handler, dte, exch):
    #pdb.set_trace()
    try:
        cmd = 'cd /datas/production/HHTICK_C/bin/'
        handler.sendline(cmd)
        print handler.readline()
        index = handler.expect(['bin', '没有那个文件或目录'])
        if index == 1:
            print('path error')
            return None
        cmd = './HHTick ../config/config_204_{}.xml {} \n'.format(exch,dte)
        handler.sendline(cmd)
        while True:
            process = handler.readline()
            print(process)
            if process.find('quit') != -1:
                print('down load SH L2 done')
                handler.sendcontrol('c')
                break
            else:
                try:
                    if int(process) < 1000:
                        print('down load error')
                        break
                except Exception,e:
                    continue
        #cmd = './HHTick ../config/config_204_SZ.xml {}'.format(dte)
        #handler.sendline(cmd)
        #while True:
        #    process = handler.readline()
        #    print(process)
        #    if process.find('quit') != -1:
        #        print('down load SZ L2 done')
        #        handler.sendcontrol('c')
        #        break
        #    else:
        #        try:
        #            if int(process) < 1000:
        #                print('down load error')
        #                break
        #        except Exception,e:
        #            continue
        
    except Exception,e:
        print 'do_download {} failed, reason:{}'.format(dte, e)
            
def del_data(dte,exch):
    try:
        handler = ssh_login(host, user, passwd)
        cmd = 'cd /datas/production/HHTICK_C/data/day/{}/'.format(exch)
        handler.sendline(cmd)
        print handler.readline()
        # index = handler.expect(['SH', '没有那个文件或目录'])
        # if index == 1:
        #     print('path error'),cmd
        #     return None
        del_cmd = 'rm -f HHTICK_{}.dat'.format(dte)
        handler.sendline(del_cmd)
        print handler.readline()
        time.sleep(1)
    except Exception,e:
        print 'del_data {} failed, reason:{}'.format(dte, e)
    #try:
    #    cmd = 'cd /datas/production/HHTICK_C/data/day/SZ/'
    #    handler.sendline(cmd)
    #    print handler.readline()
    #    # index = handler.expect(['SZ', '没有那个文件或目录'])
    #    # if index == 1:
    #    #     print('path error:'),cmd
    #    #     return None
    #    del_cmd = 'rm -f HHTICK_{}.dat'.format(dte)
    #    handler.sendline(del_cmd)
    #    print handler.readline()
    #    time.sleep(2)
    #except Exception,e:
    #    print 'del_data {} failed, reason:{}'.format(dte, e)

def down_one(dte):
    handler = ssh_login(host, user, passwd)
    if handler:
        print dte
        do_download(handler, dte, 'SH')
        do_download(handler, dte, 'SZ')
        do_download(handler, dte, 'CF')
        handler.close(force=True)
        down_load_l2(dte, 'SH')
        down_load_l2(dte, 'SZ')
        down_load_l2(dte, 'CF')
        del_data(dte, 'SH')
        del_data(dte, 'SZ')
        del_data(dte, 'CF')
def down_cal():
    td = int(datetime.datetime.today().strftime("%Y%m%d"))
    down_one(td)

    downlist = [x.strip('\n') for x in open('../config/downlist.txt','r').readlines()]
    tme = int(datetime.datetime.now().strftime("%H%M%S"))
    while tme < 200000:
        print downlist[-1]
        down_one(downlist[-1])
        downlist = downlist[0:-1]
        time.sleep(2)
        tme = int(datetime.datetime.now().strftime("%H%M%S"))
    
    #dtes = downlist[-2:] + [td]
    #downlist = downlist[:-2] 
    #handler = ssh_login(host, user, passwd)
    #if handler:
    #    for dte in dtes:
    #        print dte
    #        do_download(handler, dte)
    #    handler.close(force=True)
    #    for dte in dtes:
    #        down_load_l2(dte)
    #        del_data(dte)
    #open('../config/downlist.txt','w').write('\n'.join(downlist))
    #
    #time.sleep(3)
    dtes = downlist[-3:]
    downlist = downlist[:-3]
    handler = ssh_login(host, user, passwd)
    if handler:
        for dte in dtes:
            print dte
            do_download(handler, dte, 'SH')
            do_download(handler, dte, 'SZ')
        handler.close(force=True)
        for dte in dtes:
            down_load_l2(dte, 'SH')
            down_load_l2(dte, 'SZ')
            del_data(dte, 'SH')
            del_data(dte, 'SZ')
    open('../config/downlist.txt','w').write('\n'.join(downlist))

def get_remote_msg():
    redis_keys = ['REMOTE_DATA_CHECK_MSG']
    remote_r = redis.Redis(remote_redis_ip, remote_redis_port)
    local_r = redis.Redis(local_redis_ip, local_redis_port)
    for key in redis_keys:
        msg = remote_r.get(key)
        local_r.set(key, msg)
    
if __name__ == '__main__':
    #down_cal()
    dte = int(datetime.datetime.today().strftime("%Y%m%d"))
    if len(sys.argv) > 1:
        dte = int(sys.argv[1])
    down_one(dte)
    get_remote_msg()
