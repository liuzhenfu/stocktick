# -*- coding: utf-8 -*- #
import datetime, os
import h5py
import pysftp
import pdb
import tables
from hdfdefines import market_data, market_index
from collections import defaultdict
from hfsutils import *
from send_report import send_email
from check_l2 import check
import pexpect

host = '172.18.94.223'
user = 'root'
passwd = '123456'

'''
数据格式： 
    SZ_L2_index:dte:tkr:value(dte,high,lastPx,low,opn,pclse,tme,value,volume)  指数
    SZ_L2_market_data:dte:tkr:value(asize1-10,ask1-10,bid1-10,bsize1-10,dte,high,lastPx,low,opn,pclse,tcount,tme,value,volume)
'''

def merge_data(dte):
    try:
        # pdb.set_trace()
        datadir = '../L2data'

        fname_in = os.path.join(datadir, 'HH_TICKDB_{}.h5'.format(dte))
        fname_out = os.path.join(datadir, 'HH_TICKDB.h5')

        h5_in = tables.openFile(fname_in, mode='r')
        h5_out = tables.openFile(fname_out, mode='a', filters=tables.Filters(complib='zlib', complevel=5), title='market data futures')
        mdf_path = ['/SZ_L2_index', '/SH_L2_index', '/SZ_L2_market_data', '/SH_L2_market_data']
        for path in mdf_path:
            if path not in h5_out:
                h5_out.createGroup('/', path[1:], 'market data' if path.find('market_data')!=-1 else 'index data')

            dte_path = '{}/d{}'.format(path, dte)
            if dte_path in h5_out:
                h5_out.remove_node(path, dte) # 删除重复日期
                print 'remove ',dte_path
            h5_in.copyNode(dte_path, h5_out.getNode(path), recursive=True)
        h5_in.close()
        h5_out.close()

        subject = u'【股票L2数据处理成功】-192.168.1.216-%d' % dte
        content = u'报告时间：%s\n %s' % (
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), check_data(dte))
        send_email(['liuzhenfu@alpha2fund.com'],subject, content)

    except Exception, e:
        print >>sys.stderr,"job fail, ",e
        subject = u'【股票L2数据处理失败】-192.168.1.216-%d' % dte
        content = u'报告时间：%s\n失败原因：%s'%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),str(e))
        send_email(['liuzhenfu@alpha2fund.com'],subject, content)

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
    child.close(force=True)

def down_load_l2(dte):
    l2_file_names = ['/datas/production/HHTICK_C/data/day/SH/HHTICK_{}.dat'.format(dte),
                     '/datas/production/HHTICK_C/data/day/SZ/HHTICK_{}.dat'.format(dte)]

    scp_get('/datas/production/HHTICK_C/data/day/SH/HHTICK_{}.dat'.format(dte), '../L2data/SH/')
    scp_get('/datas/production/HHTICK_C/data/day/SZ/HHTICK_{}.dat'.format(dte), '../L2data/SZ/')
    check(dte)

if __name__ == '__main__':
    dte = int(datetime.datetime.today().strftime("%Y%m%d"))
    if len(sys.argv) > 1:
        dte = int(sys.argv[1])
    
    dtes = ['20170801', '20170802', '20170803']
    for dte in dtes:#,
        print dte
        down_load_l2(dte)

