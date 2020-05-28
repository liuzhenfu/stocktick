# -*- coding: utf-8 -*- #
import datetime, os
import pdb
from send_report import send_email
import pexpect

host = '172.18.94.223'
user = 'root'
passwd = '123456'

'''
数据格式?
    SZ_L2_index:dte:tkr:value(dte,high,lastPx,low,opn,pclse,tme,value,volume)  指数
    SZ_L2_market_data:dte:tkr:value(asize1-10,ask1-10,bid1-10,bsize1-10,dte,high,lastPx,low,opn,pclse,tcount,tme,value,volume)
'''

def down_process(transferred, total):
    print 'down load======={:.4}%:{}M/{}M'.format(float(transferred) / float(total) * 100, transferred/1024/1024, total/1024/1024)


def down_load_l2_sftp(dte):
    with pysftp.Connection(host, username=user, password=passwd) as sftp:
        with sftp.cd('/datas/production/HHTICK_C/data/day/SH'):             # temporarily chdir to public
            #sftp.put('/my/local/filename')  # upload file to public/ on remote
            l2_file_name = 'HHTICK_{}.dat.bz2'.format(dte)
            print("start down load L2 file :", l2_file_name)
            sftp.get(l2_file_name,localpath='../L2data/SH/{}'.format(l2_file_name), callback=down_process)         # get a remote file
        # temporarily chdir to public
        with sftp.cd('/datas/production/HHTICK_C/data/day/SZ'):
            #sftp.put('/my/local/filename')  # upload file to public/ on remote
            l2_file_name = 'HHTICK_{}.dat.bz2'.format(dte)
            print("start down load L2 file :", l2_file_name)
            sftp.get(l2_file_name, localpath='../L2data/SZ/{}'.format(l2_file_name), callback=down_process)         # get a remote file

# example : scp_get('/datas/a.txt', './')
def scp_get(remote_path, local_path):
    try:
        cmd = 'scp -C -p ' + user + '@' + host + ':'
        child = pexpect.spawn(cmd + remote_path + ' ' + local_path)

        index = child.expect(['(?i)password', pexpect.EOF, pexpect.TIMEOUT])
        if (index != 0):
            print('scp connect failed')
            child.close(force=True)
            return
        child.sendline(passwd)
        index = child.expect(['%', 'try again'])
        if index == 1:
            print('passwd error')
            return
        print('scp start...')
        while True:
            process = child.read(150)
            print (process)
            if process.find('100%') != -1:
                print 'scp done'
                break
        return 0
    except Exception,e:
        print 'scp_get {} failed, reason: {}'.format(remote_path, e)
        return -1

def down_load_l2(dte, exch):
    #l2_file_names = ['/datas/production/HHTICK_C/data/day/SH/HHTICK_{}.dat'.format(dte),
    #                 '/datas/production/HHTICK_C/data/day/SZ/HHTICK_{}.dat'.format(dte)]

    scp_get('/datas/production/HHTICK_C/data/day/{}/HHTICK_{}.dat'.format(exch,dte), '../L2data/{}/'.format(exch))
    #scp_get('/datas/production/HHTICK_C/data/day/SH/HHTICK_{}.dat'.format(dte), '../L2data/SH/')
    
    #check(dte)

if __name__ == '__main__':
    import sys
    dte = int(datetime.datetime.today().strftime("%Y%m%d"))
    if len(sys.argv) > 1:
        dte = int(sys.argv[1])
    
    dtes = [ '20171110' ]
    scp_get('/datas/production/HHTICK_C/data/day/SH/HHTICK_{}.dat'.format(20170724), '../L2data/SH/')

